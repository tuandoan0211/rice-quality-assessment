"""Behavior checks with known synthetic geometry; no claimed accuracy on real data."""
import tempfile
import unittest
from pathlib import Path
import cv2
import numpy as np
import pandas as pd
from preprocessing import preprocess_image
from pipeline import PipelineConfig, analyze_image, export_result
from segmentation import segment_grains
from classification import classify_grains, validate_rules
from feature_extraction import masked_glcm
from dataset_tools import prepare_dataset
from evaluate import evaluate_predictions
from image_io import read_image, write_image


def scene():
    image=np.zeros((300,500,3),np.uint8)
    cv2.ellipse(image,(90,80),(35,12),20,0,360,(220,220,220),-1)
    cv2.ellipse(image,(220,80),(18,12),-15,0,360,(220,220,220),-1)
    cv2.ellipse(image,(350,80),(35,12),40,0,360,(30,180,220),-1)
    return image


class PipelineTests(unittest.TestCase):
    def test_resize_preserves_ratio_and_original_color(self):
        image=scene()
        pre=preprocess_image(image,max_side=250,contrast='equalize')
        self.assertEqual(pre.color.shape[:2],(150,250))
        self.assertEqual(pre.scale_x,pre.scale_y)
        np.testing.assert_array_equal(pre.color,cv2.resize(image,(250,150),interpolation=cv2.INTER_AREA))

    def test_separate_grains_dual_labels_and_percentages(self):
        result=analyze_image(scene(),PipelineConfig(rules={'reference_length_px':70},texture=True))
        self.assertEqual(result.summary['total_grains'],3)
        self.assertEqual(list(result.classified.shape_label).count('Nguyên'),2)
        self.assertEqual(list(result.classified.shape_label).count('Vỡ'),1)
        self.assertEqual(list(result.classified.color_label).count('Vàng'),1)
        for _,group in result.distribution.groupby('group'):
            self.assertAlmostEqual(group.percentage.sum(),100)
        self.assertTrue(np.isfinite(result.features.select_dtypes(include=np.number)).all().all())

    def test_geometry_returns_original_units_after_resize(self):
        full=analyze_image(scene(),PipelineConfig(max_side=500))
        small=analyze_image(scene(),PipelineConfig(max_side=250))
        self.assertEqual(len(small.features),3)
        np.testing.assert_allclose(full.features.length,small.features.length,rtol=.10)

    def test_dark_foreground(self):
        result=analyze_image(255-scene(),PipelineConfig(watershed=False))
        self.assertEqual(result.summary['total_grains'],3)
        self.assertEqual(result.segmentation.foreground,'dark')

    def test_touching_grains_are_split(self):
        image=np.zeros((160,200),np.uint8)
        cv2.circle(image,(75,80),30,255,-1)
        cv2.circle(image,(120,80),30,255,-1)
        merged=segment_grains(image,watershed=False)
        split=segment_grains(image,watershed=True)
        self.assertEqual(len(merged.regions),1)
        self.assertEqual(len(split.regions),2)
        self.assertEqual(int((split.labels>0).sum()),int((split.binary>0).sum()))

    def test_single_elongated_grain_is_not_split(self):
        image=np.zeros((100,250),np.uint8)
        cv2.ellipse(image,(120,50),(90,12),0,0,360,255,-1)
        self.assertEqual(len(segment_grains(image,watershed=True).regions),1)

    def test_no_reference_means_unknown_shape(self):
        result=analyze_image(scene())
        self.assertTrue(result.classified.shape_label.eq('Không xác định').all())

    def test_border_grain_is_unknown(self):
        image=np.zeros((100,100,3),np.uint8)
        cv2.ellipse(image,(0,50),(35,15),0,0,360,(220,220,220),-1)
        result=analyze_image(image,PipelineConfig(rules={'reference_length_px':70}))
        self.assertEqual(result.classified.iloc[0].shape_label,'Không xác định')

    def test_empty_image_exports(self):
        result=analyze_image(np.zeros((100,100,3),np.uint8))
        self.assertEqual(result.summary['total_grains'],0)
        self.assertTrue((result.distribution.percentage==0).all())
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp:
            export_result(result,temp,export_rois=False)
            self.assertTrue((Path(temp)/'classification.csv').exists())

    def test_unicode_io_and_invalid_image(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp:
            path=Path(temp)/'ảnh gạo.png'
            write_image(path,scene())
            np.testing.assert_array_equal(scene(),read_image(path))
            path.write_bytes(b'not an image')
            with self.assertRaises(ValueError):
                read_image(path)

    def test_glcm_excludes_background(self):
        gray=np.full((20,20),160,np.uint8)
        mask=np.zeros((20,20),bool)
        mask[5:15,5:15]=True
        first=masked_glcm(gray,mask)
        gray[~mask]=np.arange((~mask).sum())%256
        self.assertEqual(first,masked_glcm(gray,mask))
        self.assertEqual(first['glcm_contrast'],0.0)

    def test_duplicate_images_stay_in_same_split(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp:
            root=Path(temp)
            write_image(root/'raw_dataset'/'Tot'/'one.png',scene())
            write_image(root/'batch_dataset'/'same.bmp',scene())
            frame,report=prepare_dataset(root)
            self.assertEqual(report['duplicates'],1)
            self.assertEqual(frame.split.nunique(),1)
            self.assertTrue(frame.shape_label.eq('').all())

    def test_rule_boundaries_and_color_conflict(self):
        rules=validate_rules({'reference_length_px':100})
        from classification import classify_shape,classify_color
        f=dict(length=80,feature_valid=True,touches_border=False)
        self.assertEqual(classify_shape(f,rules)[0],'Nguyên')
        f['length']=70
        self.assertEqual(classify_shape(f,rules)[0],'Không xác định')
        f['length']=69
        self.assertEqual(classify_shape(f,rules)[0],'Vỡ')
        self.assertEqual(classify_color(dict(feature_valid=True,yellow_fraction=.3,dark_fraction=.4),rules)[0],'Không xác định')
        with self.assertRaises(ValueError):
            validate_rules({'broken_max':.9,'whole_min':.8})

    def test_manual_threshold_recovers_dark_grain_and_color(self):
        image=scene()
        cv2.ellipse(image,(220,220),(35,12),0,0,360,(65,65,65),-1)
        result=analyze_image(image,PipelineConfig(threshold_override=30,rules={'reference_length_px':70}))
        self.assertEqual(result.summary['total_grains'],4)
        self.assertEqual((result.classified.color_label=='Sẫm').sum(),1)
        self.assertEqual((result.classified.color_label=='Bình thường').sum(),2)

    def test_invalid_pixel_color_ranges_rejected(self):
        with self.assertRaises(ValueError):
            analyze_image(scene(),PipelineConfig(color_rules={'yellow_h_min':50,'yellow_h_max':10}))

    def test_calibration_needs_verified_whole_grains(self):
        from calibrate import propose_reference
        image=np.zeros((300,600,3),np.uint8)
        for i in range(5):
            cv2.ellipse(image,(60+i*110,100),(35,12),0,0,360,(220,220,220),-1)
        features=analyze_image(image).features
        truth=features[['bbox_x','bbox_y','bbox_w','bbox_h']].copy()
        truth['shape_label']='Nguyên'
        truth['color_label']='Bình thường'
        truth['verified']=True
        truth['reviewer']='synthetic-test'
        config,report=propose_reference(truth,features,'fixed synthetic scale')
        self.assertAlmostEqual(config['rules']['reference_length_px'],70,delta=3)
        self.assertEqual(report['reference_whole_grains'],5)
        self.assertFalse(config['rules']['calibrated'])
        with self.assertRaises(ValueError):
            propose_reference(truth.iloc[:4],features,'fixed synthetic scale')

    def test_evaluation_requires_manual_labels_and_matches_geometry(self):
        predicted=analyze_image(scene(),PipelineConfig(rules={'reference_length_px':70})).classified
        truth=predicted[['bbox_x','bbox_y','bbox_w','bbox_h','shape_label','color_label']].copy()
        truth['verified']=False
        truth['reviewer']='synthetic-test'
        with self.assertRaises(ValueError):
            evaluate_predictions(truth,predicted)
        truth['verified']=True
        report=evaluate_predictions(truth.iloc[::-1],predicted,complete_image=True)
        self.assertEqual(report['matched_grains'],3)
        self.assertEqual(report['detection_recall'],1.0)
        self.assertEqual(report['count_absolute_error'],0)


if __name__=='__main__':
    unittest.main(verbosity=2)
