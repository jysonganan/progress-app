import pandas as pd
def time_diff_calculation(time_stamp_1, time_stamp_2, dat):
    """
    input: time_stamp_1, time_stamp_2, the column names of the input csv file
    output: the time differences data series
    """
    x1 = dat[time_stamp_1]
    x2 = dat[time_stamp_2]
    t1 = pd.to_datetime(x1)
    t2 = pd.to_datetime(x2)
    time_diff = (t2 - t1).apply(lambda x: pd.Timedelta(x).seconds/3600)
    return time_diff


def create_time_diff_group(interest_time_stamp_pairs, dat):
    """
    interest_time_stamp_pairs: list of tuples of time stamps. 
    e.g. ['specimen_collected', 'exp1_start_time', 'specimen_collected', 'exp2_start_time']
    
    output: time_diff_group: list of time difference series data. example: [time_diff_2_1, time_diff_3_1]
    output: group labels: list of group labels for histogram
    """
    time_diff_group = []
    group_labels = []
    for i in range(0, len(interest_time_stamp_pairs), 2):
        j = i+1
        time_diff = time_diff_calculation(interest_time_stamp_pairs[i], interest_time_stamp_pairs[j], dat)
        time_diff_group.append(time_diff)
        group_labels.append(interest_time_stamp_pairs[j] + '-' + interest_time_stamp_pairs[i])

    return time_diff_group, group_labels
