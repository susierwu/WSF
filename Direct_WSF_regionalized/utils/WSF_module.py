import pandas as pd
import numpy as np

# Using loc[] to Select Columns by Name
# Using iloc[] to select column by Index: df.iloc[:, 1:2]
def find_sub_df(df):
    DFlist = []
    for n in range(len(df)): 
        if df.loc[n,0] == "start_table": 
            start = n 
            #print(start)
        if df.loc[n,0] == "end_table": 
            end = n
            #print(end)
            new_df = df.loc[start+1:end-1,]      
            new_df = new_df.reset_index(drop=True)
            new_header = new_df.iloc[0] #grab the first row for the header
            new_df = new_df[1:].reset_index(drop=True) #take the data less the header row
            new_df.columns = new_header #set the header row as the df header
            DFlist.append(new_df)
    return (DFlist)



#AWARE native CF:
def find_AWARE_CF (farm_loc, aware_df): 
    aware_CF = farm_loc.copy()
    CFs = [[] for _ in range(len(farm_loc))]
    for i in range(len(farm_loc)):
        CF = []
        print("Begin searching AWARE CF for study location", i)
        index = []   # because a location could be within multiple bbox, save them to a list of available index first
        for j in range(len(aware_df)):
            if (float(farm_loc.loc[i, ['long']]) >= float(aware_df["bbox"][j][0]) and 
                float(farm_loc.loc[i, ['long']]) <= float(aware_df["bbox"][j][2]) and 
                float(farm_loc.loc[i, ['lat']]) >= float(aware_df["bbox"][j][1]) and 
                float(farm_loc.loc[i, ['lat']]) <= float(aware_df["bbox"][j][3])
               ):
                index.append(j)
                print("available AWARE CF index fall within this study location:", index)
            # if only one AWARE CF found for the study location
            if (len(index) == 1):
                CF = aware_df.iloc[index, 0:17] 
            # if study location within multiple AWARE CF bbox range,
            # save long/lat_diff between the study location and each set of AWARE_CF to a dict (ave_diff), then find closest one 
            else:
                v_diff = []      # this will be used as dict[value], dict[key] = index
                for b in aware_df.iloc[index, :]["bbox"]:
                    b_long = (b[0] + b[2])/2 
                    b_lat = (b[1] + b[3])/2
                    v_diff.append((abs(b_long - float(farm_loc.loc[i, ['long']])) + abs(b_lat - float(farm_loc.loc[i, ['lat']])) )/2)
                ave_diff = dict(zip(index, [v for v in v_diff]))
                use_index = [k for k in ave_diff.keys() if ave_diff[k] == min(ave_diff.values()) ]
                CF =  aware_df.iloc[use_index, 0:17] 

        CFs[i] = CF         #CFs.append(CF)
    
    #aware_CF = aware_CF.assign(aware_CF=CFs)
    return (CFs)




def each_farm_irri_monthlyaware_calc (farm, extract_aware_CF):   #extract_aware_CF is result from function find_AWARE_CF()
    final_all_farm_cal_list = []
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for i in range (len(farm)):
        # col_index3:15 are the 12 months irri. water for each farm, make it a new DF, 
        # sort_index() ensure both irri.water and CF ordered alphabetically A-Z (not ordered by month)
        farmx_finaldf = farm.iloc[i,3:15].sort_index().to_frame()   
        farmx_finaldf.columns = ['irri_water']
        # only one row for each eachextract_aware_CF[i], extract col_index5:17 for the 12 month AWARE_CF, assign it to a new col
        farmx_finaldf = farmx_finaldf.assign(aware_CF = np.array(extract_aware_CF[i].iloc[0,5:17].sort_index()) )  
        # multiply each month's irri water with AWARE CF for final calc and assign to a new col
        farmx_finaldf = farmx_finaldf.assign(final_aware =  farmx_finaldf["aware_CF"] * farmx_finaldf['irri_water'] )
        # reindex, sort by months, for plotting
        farmx_finaldf = farmx_finaldf.reindex(months, axis=0)
        # rename columns, for plotting, first col name -> farm.iloc[i,0:1] to extract raw farm name
        farmx_finaldf.columns = [farm.iloc[i,0:1][0] , "aware_CF [m3 world-eq / m3 consumed]", "LCIA_score [m3 world-eq]"]
        # finally append all DF to a list
        final_all_farm_cal_list.append(farmx_finaldf)
    return(final_all_farm_cal_list)