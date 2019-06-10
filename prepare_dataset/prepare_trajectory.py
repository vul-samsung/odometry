import os
import shutil
import pandas as pd


def force_make_dir(column_dst_dir):
    if os.path.exists(column_dst_dir):
        shutil.rmtree(column_dst_dir)
    os.makedirs(column_dst_dir)


def work_with_parser(root, parser):
    single_frame_df = parser.run()
    single_frame_df.reset_index(drop=True, inplace=True)
    
    image_column_preffix = 'path_to_'
    for column in single_frame_df.columns:
        if column.startswith(image_column_preffix):
            column_dst_dir = os.path.join(root, column.lstrip(image_column_preffix))
            force_make_dir(column_dst_dir)
            
            for index, elem in enumerate(single_frame_df[column]):
                _, file_extension = os.path.splitext(elem)
                assert os.path.exists(elem), elem
                symlink_path = os.path.join(column_dst_dir, '{}{}'.format(index, file_extension))
                os.symlink(elem, symlink_path)
                single_frame_df.at[index, column] = symlink_path

    return single_frame_df


def work_with_estimator(root, df, estimator):
    enriched_rows = []
    for index, row in enumerate(df.itertuples()):
        enriched_rows.append(estimator.run(root, index, row))
    enriched_df = pd.DataFrame(enriched_rows)
    del enriched_df['Index']
    return enriched_df


def transform_single_frame_df_to_paired(single_frame_df, stride):
    first_part_df = single_frame_df.iloc[:-stride].copy().reset_index(drop=True)
    second_part_df = single_frame_df.iloc[stride:].copy().reset_index(drop=True)
    second_part_df.rename(columns=lambda c: '{}_next'.format(c), inplace=True)
    return pd.concat((first_part_df, second_part_df), axis=1)


def prepare_trajectory(root,
                       parser,
                       single_frame_estimators=None, 
                       pair_frames_estimators=None,
                       stride=1):
    assert stride >= 1
    if single_frame_estimators is None:
        single_frame_estimators = []
    if pair_frames_estimators is None:
        pair_frames_estimators = []

    single_frame_df = work_with_parser(root, parser)

    for estimator in single_frame_estimators:
        single_frame_df = work_with_estimator(root, single_frame_df, estimator)

    paired_frame_df = transform_single_frame_df_to_paired(single_frame_df, stride)
    
    for estimator in pair_frames_estimators:
        paired_frame_df = work_with_estimator(root, paired_frame_df, estimator)

    return paired_frame_df
