# This file is used to test multiple class classifications.
# Algorithms tested here include: random_forest_classifier, neural_network_classifier

import unittest

import numpy as np

from healthcareai.trained_models.trained_supervised_model import TrainedSupervisedModel
import healthcareai.datasets.base as hcai_datasets

from healthcareai import AdvancedSupervisedModelTrainer
import healthcareai.tests.helpers as test_helpers
from healthcareai.common.helpers import count_unique_elements_in_column, \
    calculate_random_forest_mtry_hyperparameter
from healthcareai.common.healthcareai_error import HealthcareAIError
import healthcareai.pipelines.data_preparation as pipelines

# Set some constants to save errors and typing
CLASSIFICATION = 'classification'
CLASSIFICATION_PREDICTED_COLUMN = 'target_num'  # Number labeled target
GRAIN_COLUMN_NAME = 'PatientID'
COLUMNS_TO_REMOVE = 'target_str'


class TestAdvancedSupervisedModelTrainer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = hcai_datasets.load_dermatology()

        # Drop columns that won't help machine learning
        columns_to_remove = [COLUMNS_TO_REMOVE]
        cls.df.drop(columns_to_remove, axis=1, inplace=True)

        np.random.seed(42)

        clean_classification_df = pipelines.training_pipeline(
            CLASSIFICATION_PREDICTED_COLUMN, GRAIN_COLUMN_NAME, impute=True).fit_transform(cls.df)

        cls.classification_trainer = AdvancedSupervisedModelTrainer(
            clean_classification_df, CLASSIFICATION,
            CLASSIFICATION_PREDICTED_COLUMN)

    def test_raises_error_on_unsupported_model_type(self):
        bad_type = 'foo'
        self.assertRaises(
            HealthcareAIError,
            AdvancedSupervisedModelTrainer,
            self.df,
            bad_type,
            CLASSIFICATION_PREDICTED_COLUMN,
            GRAIN_COLUMN_NAME)

    def test_validate_classification_raises_error_on_regression(self):
        self.assertRaises(HealthcareAIError, self.classification_trainer.validate_regression)

    def test_classification_trainer_linear_regression_raises_error(self):
        self.assertRaises(HealthcareAIError, self.classification_trainer.linear_regression)


class TestRandomForestClassification(unittest.TestCase):
    def setUp(self):
        df = hcai_datasets.load_dermatology()
        # Drop uninformative columns
        df.drop([COLUMNS_TO_REMOVE], axis=1, inplace=True)

        np.random.seed(42)
        clean_df = pipelines.training_pipeline(CLASSIFICATION_PREDICTED_COLUMN,
                                               GRAIN_COLUMN_NAME, impute=True).fit_transform(df)
        self.trainer = AdvancedSupervisedModelTrainer(clean_df, CLASSIFICATION, CLASSIFICATION_PREDICTED_COLUMN)
        self.trainer.train_test_split(random_seed=0)

    def test_random_forest_no_tuning(self):
        rf = self.trainer.random_forest_classifier(trees=100, randomized_search=False)
        self.assertIsInstance(rf, TrainedSupervisedModel)
        self.assertRaises(HealthcareAIError, rf.roc_plot)
        test_helpers.assertBetween(self, 15, 30, rf.metrics['confusion_matrix'][0][0])

    def test_random_forest_tuning(self):
        max_features = calculate_random_forest_mtry_hyperparameter(4,
                                                                   'classification')
        hyperparameter_grid = {'n_estimators': [10, 20, 30],
                               'max_features': max_features}
        rf = self.trainer.random_forest_classifier(
            randomized_search=True,
            number_iteration_samples=2,
            hyperparameter_grid=hyperparameter_grid)
        self.assertIsInstance(rf, TrainedSupervisedModel)
        self.assertRaises(HealthcareAIError, rf.roc_plot)
        test_helpers.assertBetween(self, 15, 30, rf.metrics['confusion_matrix'][0][0])


class TestHelpers(unittest.TestCase):
    def test_class_counter_on_binary(self):
        df = hcai_datasets.load_dermatology()
        df.dropna(axis=0, how='any', inplace=True)
        result = count_unique_elements_in_column(df, 'target_num')
        self.assertEqual(result, 6)

    def test_class_counter_on_many(self):
        df = hcai_datasets.load_dermatology()
        result = count_unique_elements_in_column(df, 'PatientID')
        self.assertEqual(result, 366)


if __name__ == '__main__':
    unittest.main()
