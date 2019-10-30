import time
from sklearn.base import BaseEstimator


from slam.aggregation import GraphOptimizer
from slam.evaluation import calculate_metrics, normalize_metrics, average_metrics


class G2OEstimator(BaseEstimator):

    def __init__(self,
                 coef={1: 0},
                 coef_loop=0,
                 loop_threshold=0,
                 rotation_scale=1,
                 max_iterations=100,
                 online=False,
                 verbose=False,
                 rpe_indices='full'):
        self.coef = coef
        self.coef_loop = coef_loop
        self.loop_threshold = loop_threshold
        self.rotation_scale = rotation_scale
        self.max_iterations = max_iterations
        self.online = online
        self.verbose = verbose
        self.rpe_indices = rpe_indices

    @property
    def mean_cols(self):
        return ['euler_x', 'euler_y', 'euler_z', 't_x', 't_y', 't_z']

    @property
    def std_cols(self):
        return [c + '_confidence' for c in self.mean_cols]

    @property
    def all_cols(self):
        return ['from_index', 'to_index'] + self.mean_cols + self.std_cols

    def _apply_g2o_coef(self, row):
        diff = row['diff']

        std_coef = 1
        if diff in self.coef:
            std_coef = self.coef[diff]
        else:
            is_loop = diff > self.loop_threshold
            std_coef = self.coef_loop if is_loop else 1e7

        row[self.std_cols] *= std_coef
        row[['euler_x_confidence', 'euler_y_confidence', 'euler_z_confidence']] *= self.rotation_scale
        return row

    def fit(self, X, y, sample_weight=None):
        print(f'Running {self}\n')

    def predict(self, X, y):
        if self.verbose:
            start_time = time.time()
            print(f'Predicting for {len(X)} trajectories...')

        preds = []
        for i, df in enumerate(X):
            consecutive_ind = df['diff'] == 1
            print(f'\t{i + 1}. Len {len(df[consecutive_ind])}')
            df_with_coef = df.apply(self._apply_g2o_coef, axis=1)

            g2o = GraphOptimizer(max_iterations=self.max_iterations, online=self.online)
            g2o.append(df_with_coef[self.all_cols])
            predicted_trajectory = g2o.get_trajectory()
            preds.append(predicted_trajectory)

        records = list()
        for i, (gt_trajectory, predicted_trajectory) in enumerate(zip(y, preds)):
            record = calculate_metrics(gt_trajectory, predicted_trajectory, self.rpe_indices)
            print(f'Trajectory len: {len(gt_trajectory)}')
            for k, v in normalize_metrics(record).items():
                print(f'>>>{k}: {v}')
            records.append(record)

        averaged_metrics = average_metrics(records)

        if self.verbose:
            print(f'Predicting completed in {time.time() - start_time:.3f} s\n')
        return averaged_metrics
