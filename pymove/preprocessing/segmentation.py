# TODO: Arina
import numpy as np
import pandas as pd
import time
from pymove.utils.traj_utils import progress_update
from pymove.utils import constants
from pymove.utils.constants import (
	LATITUDE,
	LONGITUDE,
	DATETIME,
	TRAJ_ID,
	TID,
	UID,
	TIME_TO_PREV,
	SPEED_TO_PREV,
	DIST_TO_PREV,
	DIST_PREV_TO_NEXT,
	DIST_TO_NEXT,
	DAY,
	PERIOD,
	TYPE_PANDAS,
	TB,
	GB,
	MB,
	KB,
	B)
# """main labels """
# dic_labels = {"id" : 'id', 'lat' : 'lat', 'lon' : 'lon', 'datetime' : 'datetime'}
#
# dic_features_label = {'tid' : 'tid', 'dist_to_prev' : 'dist_to_prev', "dist_to_next" : 'dist_to_next', 'dist_prev_to_next' : 'dist_prev_to_next',
#                     'time_to_prev' : 'time_to_prev', 'time_to_next' : 'time_to_next', 'speed_to_prev': 'speed_to_prev', 'speed_to_next': 'speed_to_next',
#                     'period': 'period', 'day': 'day', 'index_grid_lat': 'index_grid_lat', 'index_grid_lon' : 'index_grid_lon',
#                     'situation':'situation'}
                

def bbox_split(bbox, number_grids):
    """splits the bounding box in N grids of the same size.

    Parameters
    ----------
    bbox: tuple
        Tuple of 4 elements, containg the minimum and maximum values of latitude and longitude of the bounding box.

    number_grids: Integer
        Determines the number of grids to split the bounding box.
        
    Returns
    -------
    df : dataframe 
        Returns the latittude and longitude coordenates of the grids after the split.
    """
    lat_min = bbox[0]
    lon_min = bbox[1]
    lat_max = bbox[2]
    lon_max = bbox[3]
    
    const_lat =  abs(abs(lat_max) - abs(lat_min))/number_grids
    const_lon =  abs(abs(lon_max) - abs(lon_min))/number_grids
    print('const_lat: {}\nconst_lon: {}'.format(const_lat, const_lon))

    df = pd.DataFrame(columns=['lat_min', 'lon_min', 'lat_max', 'lon_max'])
    for i in range(number_grids):
        df = df.append({'lat_min':lat_min, 'lon_min': lon_min + (const_lon * i), 'lat_max': lat_max, 'lon_max':lon_min + (const_lon * (i + 1))}, ignore_index=True)
    return df


def segment_trajectory_by_dist_time_speed(df_, label_id=constants.TRAJ_ID, max_dist_between_adj_points=3000, max_time_between_adj_points=7200,
                      max_speed_between_adj_points=50.0, drop_single_points=True, label_new_tid='tid_part'):
    """Segments the trajectories into clusters based on distance, time and speed.

    Parameters
    ----------
    df_ : dataframe
       The input trajectory data

    label_id : String, optional(dic_labels['id'] by default)
         Indicates the label of the id column in the user's dataframe.

    max_dist_between_adj_points : Float, optinal(3000 by default)
        Specify the maximun distance a point should have from the previous point, in order not to be dropped

    max_time_between_adj_points : Float, optinal(7200 by default)
        Specify the maximun travel time between two adjacent points

    max_speed_between_adj_points : Float, optinal(50.0 by default)
        Specify the maximun speed of travel between two adjacent points

    drop_single_points : boolean, optional(True by default)
        If set to True, drops the trajectories with only one point.

    label_new_tid : String, optional('tid_part' by default)
        The label of the column cointainig the ids of the formed clusters. Is the new splitted id.

    Note
    -----
    Time, distance and speeed features must be updated after split.
    """
        
    print('\nSplit trajectories')
    print('...max_time_between_adj_points:', max_time_between_adj_points)
    print('...max_dist_between_adj_points:', max_dist_between_adj_points)
    print('...max_speed:', max_speed_between_adj_points)
    
    try:

        if TIME_TO_PREV not in df_:
            df_.generate_dist_time_speed_features()

        if df_.index.name is None:
            print('...setting {} as index'.format(label_id))
            df_.set_index(label_id, inplace=True)

        curr_tid = 0
        if label_new_tid not in df_:
            df_[label_new_tid] = curr_tid

        ids = df_.index.unique()
        count = 0
        df_size = df_.shape[0]
        curr_perc_int = -1
        start_time = time.time()

        for idx in ids:
            curr_tid += 1
            
            filter_ = (df_.at[idx, constants.TIME_TO_PREV] > max_time_between_adj_points) | \
                        (df_.at[idx, constants.DIST_TO_PREV] > max_dist_between_adj_points) | \
                        (df_.at[idx, constants.SPEED_TO_PREV] > max_speed_between_adj_points)

            """ check if object have only one point to be removed """
            if filter_.shape == ():
                # trajectories with only one point is useless for interpolation and so they must be removed.
                count += 1
                df_.at[idx, label_new_tid] = -1
                curr_tid += -1
            else:
                tids = np.empty(filter_.shape[0], dtype=np.int64)
                tids.fill(curr_tid)
                for i, has_problem in enumerate(filter_):
                    if has_problem:
                        curr_tid += 1
                        tids[i:] = curr_tid
                count += tids.shape[0]
                df_.at[idx, label_new_tid] = tids
            
            curr_perc_int, est_time_str = progress_update(count, df_size, start_time, curr_perc_int, step_perc=20)

        if label_id == label_new_tid:
            df_.reset_index(drop=True, inplace=True)
            print('... label_id = label_new_id, then reseting and drop index')
        else:
            df_.reset_index(inplace=True)
            print('... Reseting index\n')
        
        if drop_single_points:
            shape_before_drop = df_.shape
            idx = df_[ df_[label_new_tid] == -1 ].index
            if idx.shape[0] > 0:
                print('...Drop Trajectory with a unique GPS point\n')
                ids_before_drop = df_[label_id].unique().shape[0]
                df_.drop(index=idx, inplace=True)
                print('...Object - before drop: {} - after drop: {}'.format(ids_before_drop, df_[label_id].unique().shape[0]))
                print('...Shape - before drop: {} - after drop: {}'.format(shape_before_drop, df_.shape))
                df_.generate_dist_time_speed_features()
            else:
                print('...No trajs with only one point.', df_.shape)

    except Exception as e:
        raise e


def segment_trajectory_by_speed(df_, label_id=constants.TRAJ_ID, max_speed_between_adj_points=50.0, drop_single_points=True, label_new_tid='tid_speed'):
    """Segments the trajectories into clusters based on speed.

    Parameters
    ----------
    df_ : dataframe
       The input trajectory data

    label_id : String, optional(dic_labels['id'] by default)
         Indicates the label of the id column in the user's dataframe.

    max_speed_between_adj_points : Float, optinal(50.0 by default)
        Specify the maximun speed of travel between two adjacent points

    drop_single_points : boolean, optional(True by default)
        If set to True, drops the trajectories with only one point.

    label_new_tid : String, optional('tid_speed' by default)
        The label of the column cointainig the ids of the formed clusters. Is the new splitted id.

    Note
    -----
    Speed features must be updated after split.
    """     
    print('\nSplit trajectories by max_speed_between_adj_points:', max_speed_between_adj_points) 
    try:
        if SPEED_TO_PREV not in df_:
            df_.generate_dist_time_speed_features()

        if df_.index.name is None:
            print('...setting {} as index'.format(label_id))
            df_.set_index(label_id, inplace=True)

        curr_tid = 0
        if label_new_tid not in df_:
            df_[label_new_tid] = curr_tid

        ids = df_.index.unique()
        count = 0
        df_size = df_.shape[0]
        curr_perc_int = -1
        start_time = time.time()

        for idx in ids:            
            """ increment index to trajectory"""
            curr_tid += 1

            """ filter speed max"""
            speed = (df_.at[idx, constants.SPEED_TO_PREV] > max_speed_between_adj_points)
                     
            """ check if object have only one point to be removed """
            if speed.shape == ():
                count += 1
                df_.at[idx, label_new_tid] = -1 # set object  = -1 to remove ahead
                curr_tid += -1
            else: 
                tids = np.empty(speed.shape[0], dtype=np.int64)
                tids.fill(curr_tid)
                for i, has_problem in enumerate(speed):
                    if has_problem:
                        curr_tid += 1
                        tids[i:] = curr_tid
                count += tids.shape[0]
                df_.at[idx, label_new_tid] = tids

            curr_perc_int, est_time_str = progress_update(count, df_size, start_time, curr_perc_int, step_perc=20)

        if label_id == label_new_tid:
            df_.reset_index(drop=True, inplace=True)
            print('... label_id = label_new_id, then reseting and drop index')
        else:
            df_.reset_index(inplace=True)
            print('... Reseting index\n')
       
        if drop_single_points:
            shape_before_drop = df_.shape
            idx = df_[df_[label_new_tid] == -1].index
            if idx.shape[0] > 0:
                print('...Drop Trajectory with a unique GPS point\n')
                ids_before_drop = df_[label_id].unique().shape[0]
                df_.drop(index=idx, inplace=True)
                print('...Object - before drop: {} - after drop: {}'.format(ids_before_drop, df_[label_id].unique().shape[0]))
                print('...Shape - before drop: {} - after drop: {}'.format(shape_before_drop, df_.shape))
            else:
                print('...No trajs with only one point.', df_.shape)
    except Exception as e:
        raise e


def segment_trajectory_by_time(df_, label_id=constants.TRAJ_ID, max_time_between_adj_points=900.0, drop_single_points=True, label_new_tid='tid_time'):
    """Segments the trajectories into clusters based on time.

    Parameters
    ----------
    df_ : dataframe
       The input trajectory data

    label_id : String, optional(dic_labels['id'] by default)
         Indicates the label of the id column in the user's dataframe.

    max_time_between_adj_points : Float, optinal(50.0 by default)
        Specify the maximun time of travel between two adjacent points

    drop_single_points : boolean, optional(True by default)
        If set to True, drops the trajectories with only one point.

    label_new_tid : String, optional('tid_time' by default)
        The label of the column cointainig the ids of the formed clusters. Is the new splitted id.

    Note
    -----
    Speed features must be updated after split.
    """     
    print('\nSplit trajectories by max_time_between_adj_points:', max_time_between_adj_points) 
    try:

        if TIME_TO_PREV not in df_:
            df_.generate_dist_time_speed_features()

        if df_.index.name is None:
            print('...setting {} as index'.format(label_id))
            df_.set_index(label_id, inplace=True)

        curr_tid = 0
        if label_new_tid not in df_:
            df_[label_new_tid] = curr_tid

        ids = df_.index.unique()
        count = 0
        df_size = df_.shape[0]
        curr_perc_int = -1
        start_time = time.time()

        for idx in ids:            
            """ increment index to trajectory"""
            curr_tid += 1

            """ filter time max"""
            times = (df_.at[idx, constants.TIME_TO_PREV] > max_time_between_adj_points)
                     
            """ check if object have only one point to be removed """
            if times.shape == ():
                count += 1
                df_.at[idx, label_new_tid] = -1 # set object  = -1 to remove ahead
                curr_tid += -1
            else: 
                tids = np.empty(times.shape[0], dtype=np.int64)
                tids.fill(curr_tid)
                for i, has_problem in enumerate(times):
                    if has_problem:
                        curr_tid += 1
                        tids[i:] = curr_tid
                count += tids.shape[0]
                df_.at[idx, label_new_tid] = tids

            curr_perc_int, est_time_str = progress_update(count, df_size, start_time, curr_perc_int, step_perc=20)

        if label_id == label_new_tid:
            df_.reset_index(drop=True, inplace=True)
            print('... label_id = label_new_id, then reseting and drop index')
        else:
            df_.reset_index(inplace=True)
            print('... Reseting index\n')
       
        if drop_single_points:
            shape_before_drop = df_.shape
            idx = df_[ df_[label_new_tid] == -1 ].index
            if idx.shape[0] > 0:
                print('...Drop Trajectory with a unique GPS point\n')
                ids_before_drop = df_[label_id].unique().shape[0]
                df_.drop(index=idxsegment_trajectory_by_dist_time_speed, inplace=True)
                print('...Object - before drop: {} - after drop: {}'.format(ids_before_drop, df_[label_id].unique().shape[0]))
                print('...Shape - before drop: {} - after drop: {}'.format(shape_before_drop, df_.shape))
                df_.generate_dist_time_speed_features()
            else:
                print('...No trajs with only one point.', df_.shape)
    except Exception as e:
        raise e


