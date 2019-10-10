import math
import time
import numpy as np
import pandas as pd
import dask
from dask.dataframe import DataFrame
import matplotlib.pyplot as plt
from pymove.utils.traj_utils import format_labels, shift, progress_update
from pymove.core.grid import lat_meters
from pymove.utils import transformations
from pymove.core import MoveDataFrameAbstractModel
from pymove.core.grid import create_virtual_grid
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

from pymove.utils.transformations import haversine
from datetime import datetime
import resource

#TODO: tirar o data do format_labels
#TODO: mover constantes para um arquivo
class PandasMoveDataFrame(pd.DataFrame,MoveDataFrameAbstractModel): # dask sua estrutura de dados
    def __init__(self, data, latitude=LATITUDE, longitude=LONGITUDE, datetime=DATETIME, traj_id = TRAJ_ID):
        # formatar os labels que foram passados pro que usado no pymove -> format_labels
        # renomeia as colunas do dado passado pelo novo dict
        # cria o dataframe
    
        mapping_columns = format_labels(data, traj_id, latitude, longitude, datetime)
        tdf = data.rename(columns=mapping_columns)
        if self._has_columns(tdf):
            self._validate_move_data_frame(tdf)
            #pd.DataFrame.__init__(self, tdf)
            self._data = tdf
            self._type = TYPE_PANDAS
            self._last_operation_dict = {'name': '', 'time': '', 'mem_usage': ''}

    def _has_columns(self, data):
        if(LATITUDE in data and LONGITUDE in data and DATETIME in data):
            return True
        return False

    def _validate_move_data_frame(self, data):
        # chama a função de validação   
            # deverá verificar se tem as colunas e os tipos
        try:
            if(data.dtypes.lat != 'float32'):
                data.lat.astype('float32') 
            if(data.dtypes.lon != 'float32'):
                data.lon.astype('float32') 
            if(data.dtypes.datetime != 'datetime64[ns]'):
                data.lon.astype('datetime64[ns]') 
        except AttributeError as erro:
            print(erro)

    @property
    def lat(self):
        if LATITUDE not in self:
            raise AttributeError("The MoveDataFrame does not contain the column '%s.'" % LATITUDE)
        return self._data[LATITUDE]

    @property
    def lng(self):
        if LONGITUDE not in self:
            raise AttributeError("The MoveDataFrame does not contain the column '%s.'"%LONGITUDE)
        return self._data[LONGITUDE]

    @property
    def datetime(self):
        if DATETIME not in self:
            raise AttributeError("The MoveDataFrame does not contain the column '%s.'"%DATETIME)
        return self._data[DATETIME]

    def head(self, n=5):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        
        _head = self._data.head(n)
        
        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'head'
        self._last_operation_dict['mem_usage'] = finish - init
        
        return _head

    def get_users_number(self):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        
        if UID in self._data:
            returno = self._data[UID].nunique()
        else:
            retorno = 1
        
        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'get_users_number'
        self._last_operation_dict['mem_usage'] = finish - init
        return retorno

    def to_numpy(self):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _numpy = self._data.values

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'to_numpy'
        self._last_operation_dict['mem_usage'] = finish - init
        return _numpy

    def write_file(self, file_name, separator = ','):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        self._data.to_csv(file_name, sep=separator, encoding='utf-8', index=False)

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'write_file'
        self._last_operation_dict['mem_usage'] = finish - init

    def len(self):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _len = self._data.shape[0]

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'len'
        self._last_operation_dict['mem_usage'] = finish - init
        return _len

    def to_dict(self):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _dict = self._data.to_dict()

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'to_dict'
        self._last_operation_dict['mem_usage'] = finish - init
        return _dict

    def to_grid(self, cell_size, meters_by_degree = lat_meters(-3.8162973555)):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        _grid = create_virtual_grid(cell_size, self.get_bbox(), meters_by_degree)
        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'to_grid'
        self._last_operation_dict['mem_usage'] = finish - init
        return  _grid

    #TODO: perguntar pra Arina esses que tme try, se eu deixo duplicado mesmo
    def get_bbox(self):
        """
        A bounding box (usually shortened to bbox) is an area defined by two longitudes and two latitudes, where:
            - Latitude is a decimal number between -90.0 and 90.0. 
            - Longitude is a decimal number between -180.0 and 180.0.
        They usually follow the standard format of: 
        - bbox = left, bottom, right, top 
        - bbox = min Longitude , min Latitude , max Longitude , max Latitude 
        Parameters
        ----------
        self : pandas.core.frame.DataFrame
            Represents the dataset with contains lat, long and datetime.
        
        Returns
        -------
        bbox : tuple
            Represents a bound box, that is a tuple of 4 values with the min and max limits of latitude e longitude.
        Examples
        --------
        (22.147577, 113.54884299999999, 41.132062, 121.156224)
        """
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        try:
            _bbox = (self._data[LATITUDE].min(), self._data[LONGITUDE].min(), self._data[LATITUDE].max(),self._data[LONGITUDE].max())

            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'get_bbox'
            self._last_operation_dict['mem_usage'] = finish - init
            return _bbox
        except Exception as e:
            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'get_bbox'
            self._last_operation_dict['mem_usage'] = finish - init
            raise e

    #TODO: botar inplace
    def generate_tid_based_on_id_datatime(self, str_format="%Y%m%d%H", sort=True):
        """
        Create or update trajectory id based on id e datetime.  
        Parameters
        ----------
        self : pandas.core.frame.DataFrame
            Represents the dataset with contains lat, long and datetime.
        str_format : String
            Contains informations about virtual grid, how
                - lon_min_x: longitude mínima.
                - lat_min_y: latitude miníma. 
                - grid_size_lat_y: tamanho da grid latitude. 
                - grid_size_lon_x: tamanho da longitude da grid.
                - cell_size_by_degree: tamanho da célula da Grid.
            If value is none, the function ask user by dic_grid.
        sort : boolean
            Represents the state of dataframe, if is sorted. By default it's true.
        Returns
        -------
        Examples
        --------
        ID = M00001 and datetime = 2019-04-28 00:00:56  -> tid = M000012019042800
        >>> from pymove.utils.transformations import generate_tid_based_on_id_datatime
        >>> generate_tid_based_on_id_datatime(df)
        """
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        try:
            print('\nCreating or updating tid feature...\n')
            if sort is True:
                print('...Sorting by {} and {} to increase performance\n'.format(TRAJ_ID, DATETIME))
                self._data.sort_values([TRAJ_ID, DATETIME], inplace=True)

            self._data[TID] = self._data[TRAJ_ID].astype(str) + self._data[DATETIME].dt.strftime(str_format)
            print('\n...tid feature was created...\n')

            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'generate_tid_based_on_id_datatime'
            self._last_operation_dict['mem_usage'] = finish - init
        except Exception as e:
            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'generate_tid_based_on_id_datatime'
            self._last_operation_dict['mem_usage'] = finish - init
            raise e

    # TODO complementar oq ela faz
    # TODO: botar inplace
    def generate_date_features(self):
        """
        Create or update date feature.  
        Parameters
        ----------
        self : pandas.core.frame.DataFrame
            Represents the dataset with contains lat, long and datetime.
        Returns
        -------
        Examples
        --------
        >>> from pymove.utils.transformations import generate_date_features
        >>> generate_date_features(df)
        """
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        try:
            print('Creating date features...')
            if DATETIME in self._data:
                self._data['date'] = self._data[DATETIME].dt.date
                print('..Date features was created...\n')

            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'generate_date_features'
            self._last_operation_dict['mem_usage'] = finish - init
        except Exception as e:
            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'generate_date_features'
            self._last_operation_dict['mem_usage'] = finish - init
            raise e

    # TODO complementar oq ela faz
    # TODO: botar inplace
    def generate_hour_features(self):
        """
        Create or update hour feature.  
        Parameters
        ----------
        self : pandas.core.frame.DataFrame
            Represents the dataset with contains lat, long and datetime.
        Returns
        -------
        Examples
        --------
        >>> from pymove.utils.transformations import generate_hour_features
        >>> generate_date_features(df)
        """
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        try:
            print('\nCreating or updating a feature for hour...\n')
            if DATETIME in self._data:
                self._data['hour'] = self._data[DATETIME].dt.hour
                print('...Hour feature was created...\n')

            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'generate_hour_features'
            self._last_operation_dict['mem_usage'] = finish - init
        except Exception as e:
            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'generate_hour_features'
            self._last_operation_dict['mem_usage'] = finish - init
            raise e


    # TODO: botar inplace
    def generate_day_of_the_week_features(self):
        """
        Create or update a feature day of the week from datatime.  
        Parameters
        ----------
        self : pandas.core.frame.DataFrame
            Represents the dataset with contains lat, long and datetime.
        Returns
        -------
        Examples
        --------
        Exampĺe: datetime = 2019-04-28 00:00:56  -> day = Sunday
        >>> from pymove.utils.transformations import generate_day_of_the_week_features
        >>> generate_day_of_the_week_features(df)
        """
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        try:
            print('\nCreating or updating day of the week feature...\n')
            self._data[DAY] = self._data[DATETIME].dt.day_name()
            print('...the day of the week feature was created...\n')
            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'generate_day_of_the_week_features'
            self._last_operation_dict['mem_usage'] = finish - init
        except Exception as e:
            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'generate_day_of_the_week_features'
            self._last_operation_dict['mem_usage'] = finish - init
            raise e

    # TODO: botar inplace
    def generate_time_of_day_features(self):
        """
        Create a feature time of day or period from datatime.
        Parameters
        ----------
        self : pandas.core.frame.DataFrame
            Represents the dataset with contains lat, long and datetime.
        Returns
        -------
        Examples
        --------
        - datetime1 = 2019-04-28 02:00:56 -> period = early morning
        - datetime2 = 2019-04-28 08:00:56 -> period = morning
        - datetime3 = 2019-04-28 14:00:56 -> period = afternoon
        - datetime4 = 2019-04-28 20:00:56 -> period = evening
        >>> from pymove.utils.transformations import generate_time_of_day_features
        >>> generate_time_of_day_features(df)
        """
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        try:
            print(
                '\nCreating or updating period feature\n...early morning from 0H to 6H\n...morning from 6H to 12H\n...afternoon from 12H to 18H\n...evening from 18H to 24H')
            conditions = [(self._data[DATETIME].dt.hour >= 0) & (self._data[DATETIME].dt.hour < 6),
                          (self._data[DATETIME].dt.hour >= 6) & (self._data[DATETIME].dt.hour < 12),
                          (self._data[DATETIME].dt.hour >= 12) & (self._data[DATETIME].dt.hour < 18),
                          (self._data[DATETIME].dt.hour >= 18) & (self._data[DATETIME].dt.hour < 24)]
            choices = ['early morning', 'morning', 'afternoon', 'evening']
            self._data[PERIOD] = np.select(conditions, choices, 'undefined')
            print('...the period of day feature was created')

            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'generate_time_of_day_features'
            self._last_operation_dict['mem_usage'] = finish - init
        except Exception as e:
            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'generate_time_of_day_features'
            self._last_operation_dict['mem_usage'] = finish - init
            raise e

    # TODO complementar oq ela faz
    # TODO: botar inplace
    def generate_dist_features(self, label_id=TRAJ_ID, label_dtype=np.float64, sort=True):
        """
         Create three distance in meters to an GPS point P (lat, lon).
        Parameters
        ----------
        self : pandas.core.frame.DataFrame
            Represents the dataset with contains lat, long and datetime.
        label_id : String
            Represents name of column of trajectore's id. By default it's 'id'.
        label_dtype : String
            Represents column id type. By default it's np.float64.
        sort : boolean
            Represents the state of dataframe, if is sorted. By default it's true.
        Returns
        -------
        Examples
        --------
        Example:    P to P.next = 2 meters
                    P to P.previous = 1 meter
                    P.previous to P.next = 1 meters
        >>> from pymove.utils.transformations import generate_dist_features
        >>> generate_dist_features(df)
        """
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        try:
            print('\nCreating or updating distance features in meters...\n')
            start_time = time.time()

            if sort is True:
                print('...Sorting by {} and {} to increase performance\n'.format(label_id, DATETIME))
                self._data.sort_values([label_id, DATETIME], inplace=True)

            if self._data.index.name is None:
                print('...Set {} as index to increase attribution performance\n'.format(label_id))
                self._data.set_index(label_id, inplace=True)

            """ create ou update columns"""
            self._data[DIST_TO_PREV] = label_dtype(-1.0)
            self._data[DIST_TO_NEXT] = label_dtype(-1.0)
            self._data[DIST_PREV_TO_NEXT] = label_dtype(-1.0)

            ids = self._data.index.unique()
            selfsize = self._data.shape[0]
            curr_perc_int = -1
            start_time = time.time()
            deltatime_str = ''
            sum_size_id = 0
            size_id = 0
            for idx in ids:
                curr_lat = self._data.at[idx, LATITUDE]
                curr_lon = self._data.at[idx, LONGITUDE]

                size_id = curr_lat.size

                if size_id <= 1:
                    print('...id:{}, must have at least 2 GPS points\n'.format(idx))
                    self._data.at[idx, DIST_TO_PREV] = np.nan

                else:
                    prev_lat = shift(curr_lat, 1)
                    prev_lon = shift(curr_lon, 1)
                    # compute distance from previous to current point
                    self._data.at[idx, DIST_TO_PREV] = haversine(prev_lat, prev_lon, curr_lat, curr_lon)

                    next_lat = shift(curr_lat, -1)
                    next_lon = shift(curr_lon, -1)
                    # compute distance to next point
                    self._data.at[idx, DIST_TO_NEXT] = haversine(curr_lat, curr_lon, next_lat, next_lon)

                    # using pandas shift in a large dataset: 7min 21s
                    # using numpy shift above: 33.6 s

                    # use distance from previous to next
                    self._data.at[idx, DIST_PREV_TO_NEXT] = haversine(prev_lat, prev_lon, next_lat, next_lon)

                    sum_size_id += size_id
                    curr_perc_int, est_time_str = progress_update(sum_size_id, selfsize, start_time, curr_perc_int,
                                                                  step_perc=20)
            self._data.reset_index(inplace=True)
            print('...Reset index\n')
            print('..Total Time: {}'.format((time.time() - start_time)))

            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'generate_dist_features'
            self._last_operation_dict['mem_usage'] = finish - init
        except Exception as e:
            print('label_id:{}\nidx:{}\nsize_id:{}\nsum_size_id:{}'.format(label_id, idx, size_id, sum_size_id))
            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'generate_dist_features'
            self._last_operation_dict['mem_usage'] = finish - init
            raise e


    # TODO: botar inplace
    def generate_dist_time_speed_features(self, label_id=TRAJ_ID, label_dtype=np.float64, sort=True):
        """
        Firstly, create three distance to an GPS point P (lat, lon)
        After, create two feature to time between two P: time to previous and time to next 
        Lastly, create two feature to speed using time and distance features
        Parameters
        ----------
        self : pandas.core.frame.DataFrame
            Represents the dataset with contains lat, long and datetime.
        label_id : String
            Represents name of column of trajectore's id. By default it's 'id'.
        label_dtype : String
            Represents column id type. By default it's np.float64.
        sort : boolean
            Represents the state of dataframe, if is sorted. By default it's true.
        Returns
        -------
        Examples
        --------
        Example:    dist_to_prev =  248.33 meters, dist_to_prev 536.57 meters
                    time_to_prev = 60 seconds, time_prev = 60.0 seconds
                    speed_to_prev = 4.13 m/s, speed_prev = 8.94 m/s.
        >>> from pymove.utils.transformations import generate_dist_time_speed_features
        >>> generate_dist_time_speed_features(df)
        """
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        try:

            print('\nCreating or updating distance, time and speed features in meters by seconds\n')
            start_time = time.time()

            if sort is True:
                print('...Sorting by {} and {} to increase performance\n'.format(label_id, DATETIME))
                self._data.sort_values([label_id, DATETIME], inplace=True)

            if self._data.index.name is None:
                print('...Set {} as index to a higher peformance\n'.format(label_id))
                self._data.set_index(label_id, inplace=True)

            """create new feature to time"""
            self._data[DIST_TO_PREV] = label_dtype(-1.0)

            """create new feature to time"""
            self._data[TIME_TO_PREV] = label_dtype(-1.0)

            """create new feature to speed"""
            self._data[SPEED_TO_PREV] = label_dtype(-1.0)

            ids = self._data.index.unique()
            selfsize = self._data.shape[0]
            curr_perc_int = -1
            sum_size_id = 0
            size_id = 0

            for idx in ids:
                curr_lat = self._data.at[idx, LATITUDE]
                curr_lon = self._data.at[idx, LONGITUDE]

                size_id = curr_lat.size

                if size_id <= 1:
                    print('...id:{}, must have at least 2 GPS points\n'.format(idx))
                    self._data.at[idx, DIST_TO_PREV] = np.nan
                    self._data.at[idx, TIME_TO_PREV] = np.nan
                    self._data.at[idx, SPEED_TO_PREV] = np.nan
                else:
                    prev_lat = shift(curr_lat, 1)
                    prev_lon = shift(curr_lon, 1)
                    prev_lon = shift(curr_lon, 1)
                    # compute distance from previous to current point
                    self._data.at[idx, DIST_TO_PREV] = haversine(prev_lat, prev_lon, curr_lat, curr_lon)

                    time_ = self._data.at[idx, DATETIME].astype(label_dtype)
                    time_prev = (time_ - shift(time_, 1)) * (10 ** -9)
                    self._data.at[idx, TIME_TO_PREV] = time_prev

                    """ set time_to_next"""
                    # time_next = (ut.shift(time_, -1) - time_)*(10**-9)
                    # self.at[idx, dic_features_label['time_to_next']] = time_next

                    "set Speed features"
                    self._data.at[idx, SPEED_TO_PREV] = self._data.at[idx, DIST_TO_PREV] / (time_prev)  # unit: m/s

                    sum_size_id += size_id
                    curr_perc_int, est_time_str = progress_update(sum_size_id, selfsize, start_time, curr_perc_int,
                                                                  step_perc=20)
            print('...Reset index...\n')
            self._data.reset_index(inplace=True)
            print('..Total Time: {:.3f}'.format((time.time() - start_time)))

            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'generate_dist_time_speed_features'
            self._last_operation_dict['mem_usage'] = finish - init
        except Exception as e:
            print('label_id:{}\nidx:{}\nsize_id:{}\nsum_size_id:{}'.format(label_id, idx, size_id, sum_size_id))
            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'generate_dist_time_speed_features'
            self._last_operation_dict['mem_usage'] = finish - init
            raise e


    # TODO: botar inplace
    def generate_move_and_stop_by_radius(self, radius=0, target_label=DIST_TO_PREV):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        if DIST_TO_PREV not in self._data:
            self._data.generate_dist_features()
        try:
            print('\nCreating or updating features MOVE and STOPS...\n')
            conditions = (self._data[target_label] > radius), (self._data[target_label] <= radius)
            choices = ['move', 'stop']

            self._data["situation"] = np.select(conditions, choices, np.nan)
            print('\n....There are {} stops to this parameters\n'.format(self._data[self._data["situation"] == 'stop'].shape[0]))

            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'generate_move_and_stop_by_radius'
            self._last_operation_dict['mem_usage'] = finish - init
        except Exception as e:
            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'generate_move_and_stop_by_radius'
            self._last_operation_dict['mem_usage'] = finish - init
            raise e

    def time_interval(self):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        time_diff = self._data[DATETIME].max() - self._data[DATETIME].min()

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'time_interval'
        self._last_operation_dict['mem_usage'] = finish - init
        return time_diff

    def plot_all_features(self, figsize=(21, 15), dtype=np.float64, save_fig=True, name='features.png'):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        try:
            col_float = self._data.select_dtypes(include=[dtype]).columns
            tam = col_float.size
            if (tam > 0):
                fig, ax = plt.subplots(tam, 1, figsize=figsize)
                ax_count = 0
                for col in col_float:
                    ax[ax_count].set_title(col)
                    self._data[col].plot(subplots=True, ax=ax[ax_count])
                    ax_count += 1

                if save_fig:
                    plt.savefig(fname=name, fig=fig)

            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'plot_all_features'
            self._last_operation_dict['mem_usage'] = finish - init
        except Exception as e:
            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'plot_all_features'
            self._last_operation_dict['mem_usage'] = finish - init
            raise e

    def plot_trajs(self, figsize=(10,10), return_fig=True, markers= 'o',markersize=20):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        fig = plt.figure(figsize=figsize)
        ids = self._data["id"].unique()
        
        for id_ in ids:
            selfid = self._data[ self._data["id"] == id_ ]
            plt.plot(selfid[LONGITUDE], selfid[LATITUDE], markers, markersize=markersize)

            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'plot_trajs'
            self._last_operation_dict['mem_usage'] = finish - init
        if return_fig:
            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'plot_trajs'
            self._last_operation_dict['mem_usage'] = finish - init
            return fig

    def plot_traj_id(self, tid, figsize=(10,10)):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        fig = plt.figure(figsize=figsize)
        if TID not in self._data:
            self.generate_tid_based_on_id_datatime()
        self._data = self._data[self._data[TID] == tid ]
        plt.plot(self._data.iloc[0][LONGITUDE], self._data.iloc[0][LATITUDE], 'yo', markersize=20)             # start point
        plt.plot(self._data.iloc[-1][LONGITUDE], self._data.iloc[-1][LATITUDE], 'yX', markersize=20)           # end point
        
        if 'isNode'not in self:
            plt.plot(self._data[LONGITUDE], self._data[LATITUDE])
            plt.plot(self._data.loc[:, LONGITUDE], self._data.loc[:, LATITUDE], 'r.', markersize=8)  # points
        else:
            filter_ = self._data['isNode'] == 1
            selfnodes = self._data.loc[filter_]
            selfpoints = self._data.loc[~filter_]
            plt.plot(selfnodes[LONGITUDE], selfnodes[LATITUDE], linewidth=3)
            plt.plot(selfpoints[LONGITUDE], selfpoints[LATITUDE])
            plt.plot(selfnodes[LONGITUDE], selfnodes[LATITUDE], 'go', markersize=10)   # nodes
            plt.plot(selfpoints[LONGITUDE], selfpoints[LATITUDE], 'r.', markersize=8)  # points


        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'plot_traj_id'
        self._last_operation_dict['mem_usage'] = finish - init
        return self._data, fig

    def show_trajectories_info(self):
        """
        Show dataset information from dataframe, this is number of rows, datetime interval, and bounding box.
        Parameters
        ----------
        self : pandas.core.frame.DataFrame
            Represents the dataset with contains lat, long and datetime.
        dic_labels : dict
            Represents mapping of column's header between values passed on params.
        Returns
        -------
        Examples
        --------
        >>> from pymove.utils.utils import show_trajectories_info
        >>> show_trajectories_info(df)
        ======================= INFORMATION ABOUT DATASET =======================
        Number of Points: 217654
        Number of IDs objects: 2
        Start Date:2008-10-23 05:53:05     End Date:2009-03-19 05:46:37
        Bounding Box:(22.147577, 113.54884299999999, 41.132062, 121.156224)
        =========================================================================
        """
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        try:
            print('\n======================= INFORMATION ABOUT DATASET =======================\n')
            print('Number of Points: {}\n'.format(self._data.shape[0]))
            if TRAJ_ID in self._data:
                print('Number of IDs objects: {}\n'.format(self._data[TRAJ_ID].nunique()))
            if TID in self._data:
                print('Number of TIDs trajectory: {}\n'.format(self._data[TID].nunique()))
            if DATETIME in self._data:
                print('Start Date:{}     End Date:{}\n'.format(self._data[DATETIME].min(),
                                                               self._data[DATETIME].max()))
            if LATITUDE and LONGITUDE in self._data:
                print('Bounding Box:{}\n'.format(
                    self.get_bbox()))  # bbox return =  Lat_min , Long_min, Lat_max, Long_max)
            if TIME_TO_PREV in self._data:
                print(
                    'Gap time MAX:{}     Gap time MIN:{}\n'.format(
                        round(self._data[TIME_TO_PREV].max(), 3),
                        round(self._data[TIME_TO_PREV].min(), 3)))
            if SPEED_TO_PREV in self._data:
                print('Speed MAX:{}    Speed MIN:{}\n'.format(round(self._data[SPEED_TO_PREV].max(), 3),
                                                              round(self._data[SPEED_TO_PREV].min(), 3)))
            if DIST_TO_PREV in self._data:
                print('Distance MAX:{}    Distance MIN:{}\n'.format(
                    round(self._data[DIST_TO_PREV].max(), 3),
                    round(self._data[DIST_TO_PREV].min(),
                          3)))

            print('\n=========================================================================\n')


            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'show_trajectories_info'
            self._last_operation_dict['mem_usage'] = finish - init
        except Exception as e:
            finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            self._last_operation_dict['time'] = time.time() - start
            self._last_operation_dict['name'] = 'show_trajectories_info'
            self._last_operation_dict['mem_usage'] = finish - init
            raise e

    def min(self, axis=None, skipna=None, level=None, numeric_only=None, **kwargs):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _min = self._data.min(axis, skipna, level, numeric_only, **kwargs)

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'min'
        self._last_operation_dict['mem_usage'] = finish - init
        return _min

    def max(self, axis=None, skipna=None, level=None, numeric_only=None, **kwargs):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _max = self._data.max(axis, skipna, level, numeric_only, **kwargs)

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'max'
        self._last_operation_dict['mem_usage'] = finish - init
        return _max

    def count(self, axis=0, level=None, numeric_only=False):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _count = self._data.count(axis, level, numeric_only)

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'count'
        self._last_operation_dict['mem_usage'] = finish - init
        return _count

    def groupby(self, by=None, axis=0, level=None, as_index=True, sort=True, group_keys=True, squeeze=False,
                observed=False, **kwargs):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _groupby = self._data.groupby(by, axis, level, as_index, sort, group_keys, squeeze, observed, **kwargs)

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'groupby'
        self._last_operation_dict['mem_usage'] = finish - init
        return _groupby

    def drop_duplicates(self, subset=None, keep='first', inplace=False):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _drop_duplicates = self._data.drop_duplicates(subset, keep, inplace)

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'drop_duplicates'
        self._last_operation_dict['mem_usage'] = finish - init
        return _drop_duplicates

    def reset_index(self,  level=None, drop=False, inplace=False, col_level=0, col_fill=''):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _reset_index = self._data.reset_index(level, drop, inplace, col_level, col_fill)

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'reset_index'
        self._last_operation_dict['mem_usage'] = finish - init
        return _reset_index

    #TODO: duvida sobre erro quando sem paraetros, perguntar dd
    def plot(self, *args, **kwargs):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _plot = self._data.plot(*args, **kwargs)

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'plot'
        self._last_operation_dict['mem_usage'] = finish - init
        return _plot

    def select_dtypes(self, include=None, exclude=None):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _select_dtypes = self._data.select_dtypes(include, exclude)

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'select_dtypes'
        self._last_operation_dict['mem_usage'] = finish - init
        return _select_dtypes

    def sort_values(self, by, axis=0, ascending=True, inplace=False, kind='quicksort', na_position='last'):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _sort_values = self._data.sort_values(by, axis, ascending, inplace, kind, na_position)

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = '_sort_values'
        self._last_operation_dict['mem_usage'] = finish - init
        return _sort_values

    def astype(self, dtype, copy=True, errors='raise', **kwargs):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _astype = self._data.astype(dtype, copy, errors, **kwargs)

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'astype'
        self._last_operation_dict['mem_usage'] = finish - init
        return _astype

    def set_index(self, keys, drop=True, append=False, inplace=False, verify_integrity=False):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _set_index = self._data.set_index(keys, drop, append, inplace, verify_integrity)

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = '_set_index'
        self._last_operation_dict['mem_usage'] = finish - init
        return _set_index

    def drop(self, labels=None, axis=0, index=None, columns=None, level=None, inplace=False, errors='raise'):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _drop = self._data.drop(labels, axis, index, columns, level, inplace, errors)

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'drop'
        self._last_operation_dict['mem_usage'] = finish - init
        return _drop

    def duplicated(self, subset=None, keep='first'):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _duplicated = self._data.duplicated(subset, keep)

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'duplicated'
        self._last_operation_dict['mem_usage'] = finish - init
        return _duplicated

    def shift(self, periods=1, freq=None, axis=0, fill_value=None):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _shift = self._data.shift(periods, freq, axis, fill_value)

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'shift'
        self._last_operation_dict['mem_usage'] = finish - init
        return _shift

    def any(self, axis=0, bool_only=None, skipna=True, level=None, **kwargs):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _any = self._data.any(axis, bool_only, skipna, level, **kwargs)

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'any'
        self._last_operation_dict['mem_usage'] = finish - init
        return _any

    def dropna(self, axis=0, how='any', thresh=None, subset=None, inplace=False):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _dropna = self._data.dropna(axis, how, thresh, subset, inplace)

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'dropna'
        self._last_operation_dict['mem_usage'] = finish - init
        return _dropna

    def isin(self, values):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _isin = self._data.isin(values)

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'isin'
        self._last_operation_dict['mem_usage'] = finish - init
        return _isin

    def append(self, other, ignore_index=False, verify_integrity=False, sort=None):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        _append = self._data.append(other, ignore_index, verify_integrity, sort)

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'append'
        self._last_operation_dict['mem_usage'] = finish - init
        return _append

    def nunique(self, axis=0, dropna=True):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        return self._data.nunique(axis, dropna)

    #TODO: botar os parâmetros
    def to_csv(self, file_name, sep=',', encoding=None):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        self._data.to_csv(file_name, sep, encoding)

        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'to_csv'
        self._last_operation_dict['mem_usage'] = finish - init

    def to_dask(self):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        from pymove.core.DaskMoveDataFrame import DaskMoveDataFrame as dm

        _dask = dm(self._data, latitude=LATITUDE, longitude=LONGITUDE, datetime=DATETIME, traj_id=TRAJ_ID, n_partitions=1)
        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'to_dask'
        self._last_operation_dict['mem_usage'] = finish - init
        return _dask

    def to_pandas(self):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'to_pandas'
        self._last_operation_dict['mem_usage'] = finish - init
        return self._data

    def get_type(self):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


        finish = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._last_operation_dict['time'] = time.time() - start
        self._last_operation_dict['name'] = 'get_type'
        self._last_operation_dict['mem_usage'] = finish - init
        return self._type

    def last_operation_time(self):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        return self._last_operation_dict['time']

    def last_operation_name(self):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        return self._last_operation_dict['name']

    def last_operation(self):
        start = time.time()
        init = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        return self._last_operation_dict

    #TODO: Ver se os cálculos estão ok
    def mem(self, format):
        switcher = {
            B: self._last_operation_dict.mem_usage,
            KB: self._last_operation_dict.mem_usage / 1024,
            MB: self._last_operation_dict.mem_usage / (1024 * 2),
            GB: self._last_operation_dict.mem_usage / (1024 * 3),
            TB: self._last_operation_dict.mem_usage / (1024 * 4),
        }

        return switcher.format

    # TODO: AJEITAR ESSES 2
    # def __setattr__(atributo, coluna, indice, valor):
    #   atributo.loc[indice, coluna] = valor
    #   # self.__dict__[name] = value
    #
    #
    # def __getattr__(atributo, indice, coluna):
    #   print("entrou aqui")
    #   return atributo.loc[indice, coluna]



