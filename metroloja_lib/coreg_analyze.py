import os, glob, time, datetime, pathlib, shutil
import plotly.graph_objects as go
import plotly.express as px
import tkinter as tk
import pandas as pd

from alive_progress import alive_bar
from tkinter import filedialog as fd
from PyPDF2 import PdfFileMerger
from functools import reduce
from scipy import stats

def select_folder():
    root = tk.Tk()
    root.withdraw()


    folder_selected = fd.askdirectory() 
    date_file = os.listdir(folder_selected)
    for i in date_file:
        if i.startswith('.'):
            date_file.remove(i)

    for i in date_file:
        if i == 'pdf_result':
            date_file.remove(i)

    f_folder = []
    for fl in date_file:
        f_folder.append(os.path.join(folder_selected, fl))

    all_image_name = []

    for k in range(len(f_folder)):
        l = []
        for path in glob.glob(f'{f_folder[k]}/*/**/', recursive=True):
            l.append(path)
        path_name = [l[i] for i in range(0,len(l),2)]

        img_name = []
        for j in path_name:
            TempPath = pathlib.PurePath(j)
            img_name.append(TempPath.name)

        del img_name[0]
        all_image_name.append(img_name)
        
        
    print('Images name :')
    for indx in range(len(all_image_name)):
        allimages = all_image_name[indx]
        for i in range(len(allimages)-1):
            n = os.path.normpath(allimages[i])
            path_split = n.split(os.sep)
            f_n = path_split[-1]
            if f_n.startswith(".") == True:
                allimages.remove(allimages[i])
        for rm in allimages:
            if rm == 'Processed':
                allimages.remove(rm)
    len_tot_image = reduce(lambda count, l: count + len(l), all_image_name, 0)


    lf_name = []
    for indx in range(len(all_image_name)):
        print(f'Date {indx + 1}')
        allimages = all_image_name[indx]
        for j in allimages:
            print(f'   {j}')
            lf_name.append(j)
    
    return(folder_selected, date_file, all_image_name, lf_name, len_tot_image)





def processed_path(folder_selected, date_file):
    len_bar = (len(date_file)-1)*2
    print('Path of processed folder : \n')
    all_processed_path = []
    for j in date_file:
        dt_path = os.path.join(folder_selected, j)
        processed_path = os.path.join(dt_path,'Processed')

        for i in os.listdir(processed_path):
            try:
                if i.startswith('.') == False:
                    processed_path2 = os.path.join(processed_path,i)
                    print(processed_path2)
                    all_processed_path.append(processed_path2)
                    
            except:
                print('No metroloJ_QC result')
    return(all_processed_path)






def convert_to_df(all_processed_path, date_file, all_image_name, lf_name, len_tot_image, folder_selected):
    DF_coreg = pd.DataFrame()
    DF_coreg_noComb = pd.DataFrame()
    idx = 0
    for process in all_processed_path:
        # r=root, d=directories, f = files
        for r, d, f in os.walk(process):
            for file in f:
                if file == "summary.xls":
                    f_path = os.path.join(r, file)
                    TempName = all_image_name[idx]
                    for i in range(len(TempName)):
                        grp = TempName[i]
                        path_split = process.split(os.sep)

                        filename = grp
                        initTempDate = path_split[-3]
                        date = datetime.datetime.strptime(initTempDate, '%Y%m%d').date()
                        microscope = f'{path_split[-5]} : {path_split[-4]}'
                        '''
                        for fn in lf_name:
                            if fn in grp:
                                fn2 = fn.replace(' ','')
                        '''

                        data = pd.read_csv(f_path, sep = "\t", header=None, names=range(8))
                        #data = pd.read_csv(f_path,
                        data = data.iloc[:, :-1] # Drop the last column

                        table_names = ["Ratios", "Raw Ratios", "Pixel shift", "Calibrated distances (in µm)", "Raw calibrated distancesµm)"]
                        groups = data[0].isin(table_names).cumsum()
                        tables = {g.iloc[0,0]: g.iloc[1:] for k,g in data.groupby(groups)} #dictionnary of each selected table 

                        df_ratios = tables["Raw Ratios"]
                        df_distances = tables["Raw calibrated distancesµm)"]

                        # Reindex column name
                        df_ratios = df_ratios.reset_index(drop=True)
                        df_ratios.columns = df_ratios.iloc[0]
                        df_ratios = df_ratios.reindex(df_ratios.index.drop(0)).reset_index(drop=True)
                        df_ratios.columns.name = None


                        df_distances = df_distances.reset_index(drop=True)
                        df_distances.columns = df_distances.iloc[0]
                        df_distances = df_distances.reindex(df_distances.index.drop(0)).reset_index(drop=True)
                        df_distances.columns.name = None


                        # Reindex row name
                        df_ratios = df_ratios.set_index('Combinations')

                        df_distances = df_distances.set_index('Combinations')


                        # Create dataframe
                        CombList = df_ratios.columns
                        for comb in CombList:
                            comb_val_ratio = df_ratios.loc[grp, comb]
                            comb_val_dist = df_distances.loc[grp, comb]

                            TempDataList = pd.DataFrame({'Date':[date], "Microscope":[microscope], "Image Name":[grp], "Combination":[comb], 'Distances (µm)':[comb_val_dist], 'Ratios':[comb_val_ratio]})
                            DF_coreg = pd.concat([DF_coreg,TempDataList])

                        TempDataList2 = pd.DataFrame({'Date':[date], "Microscope":[microscope], "Image Name":[grp]})
                        DF_coreg_noComb = pd.concat([DF_coreg_noComb,TempDataList2])
                        #DF_coreg_noComb  = DF_coreg_noComb.groupby(['Date', 'Image Name']).size().reset_index(name='n')
                        DF_coreg_noComb2 = DF_coreg_noComb.groupby(['Date']).size().reset_index(name='n')
                        
        idx += 1
                                
    DF_coreg.reset_index(drop=True, inplace=True)
    
    return(DF_coreg, DF_coreg_noComb2, df_distances.columns)

                            

    

    
def coreg_stats(DF_coreg0, DF_coreg1):
    '''
    DF_coreg = DF_coreg.explode('Distances (µm)')
    DF_coreg['Distances (µm)'] = DF_coreg['Distances (µm)'].astype('float')
    '''
    
    #eff_df  = DF_coreg0.groupby(['Date']).size().reset_index(name='n')
    median_df_dist = DF_coreg0.groupby(['Date', 'Microscope', 'Combination'])['Distances (µm)'].median().to_frame('Distances Median').reset_index()
    max_df_dist  = DF_coreg0.groupby(['Date', 'Microscope', 'Combination'])['Distances (µm)'].max().to_frame('Distances Max').reset_index()
    median_df_ratio = DF_coreg0.groupby(['Date', 'Microscope', 'Combination'])['Ratios'].median().to_frame('Ratios Median').reset_index()
    max_df_ratio  = DF_coreg0.groupby(['Date', 'Microscope', 'Combination'])['Ratios'].max().to_frame('Ratios Max').reset_index()


    allStat = [median_df_dist, max_df_dist, median_df_ratio, max_df_ratio]
    df_MedStd = reduce(lambda  left,right: pd.merge(left,right,on=['Date', 'Microscope', 'Combination'], how='outer'), allStat)
    df_MedStd = df_MedStd.merge(DF_coreg1, on='Date', how='outer')

    leg_dict = {}
    for i in range(len(df_MedStd)):
        t = df_MedStd['Date'].iloc[i]
        leg_dict[str(t)] = str(t) + ' (n = ' + str(df_MedStd['n'].iloc[i]) + ')'

    return(df_MedStd, leg_dict)






def select_param():
    master = tk.Tk()
    master.geometry("300x100")
    master.title('Check all the measurements you want to plot')

    values = ["Distances (µm)", "Ratios"]

    states_list = []
    for text in values:
        check = tk.StringVar(master)
        check_but = tk.Checkbutton(master, text = text, variable = check,
                                   onvalue = text, offvalue = 'off', command=check.get())
        check_but.pack(padx=0.5, pady=0.5, anchor=tk.W)
        states_list.append(check)

    button = tk.Button(
        master,
        text="Get Selected",
        command=master.quit)
    button.pack(fill=tk.X, padx=5, pady=5)
    
    

    btn = tk.Button(master,text="Close", command=master.quit)
    btn.pack(pady = 5)


    master.mainloop()
    master.destroy()

    print("Selection :")
    selected_param = []
    for v in states_list:
        if v.get()!='':
            selected_param.append(v.get())
            print(f"  * {v.get()}")

    return(selected_param, values)




def create_box(df, param, table_column_param, med_column_param, im_path,
               result, ttest_table_column, leg_dict, sys_name, DC_var, df_MedStd, date_list):
    date1 = date_list
    date2 = date1.copy()
    date2[0] = "first date"
    
    df = df.explode(table_column_param)
    df[table_column_param] = df[table_column_param].astype('float')
    

    fig = px.box(df, x = "Date", y = table_column_param, color = "Date", category_orders={"Date" : date1},
                 facet_row="Combination", title = f"{sys_name[0]}           {param} Box plot           PICT-BDD           (Update : {datetime.datetime.today().strftime('%Y-%m-%d')})<br><sub><b>Statistical T-Tests are carried out between a date and the date immediately preceding it</b></sub>", points="outliers", height=2000, width=900).update_yaxes(matches=None)

    fig.update_layout(showlegend=True)
    fig.update_layout(title_x=0.5)
    
    
    
    fig.for_each_trace(lambda t: t.update(name = leg_dict[t.name],
                                          legendgroup = leg_dict[t.name],
                                          hovertemplate = t.hovertemplate.replace(t.name, leg_dict[t.name])
                                         )
                      )


    '''
    main = tk.Tk()
    main.withdraw()
    main.geometry("100x100")

    range_result = tk.messagebox.askquestion(f"{table_column_param} plot", "Do you want to put your figures on the same scale?")
    '''
        
    listAllComb = list(DC_var.keys())
    nb_listAllComb = len(listAllComb)
    for lac in listAllComb:
        TempDF_Med = DC_var[lac]
        Which_channel = TempDF_Med['Combination'][0]

        fig.add_trace(
            go.Scatter(x=TempDF_Med["Date"].tolist(), y=TempDF_Med[med_column_param].tolist(), showlegend=False, mode='lines+markers',
                       line=dict(color="#000000")), row=nb_listAllComb, col=1
        )

        '''
        max_df = df.groupby(['Date', 'Microscope', 'Combination'])[table_column_param].max().to_frame('max').reset_index()
        min_df = df.groupby(['Date', 'Microscope', 'Combination'])[table_column_param].min().to_frame('min').reset_index()

        merge_MinMax = pd.merge(min_df, max_df, how='left', on=['Date', 'Microscope', 'Combination'])

        
        
        
        # Select range for boxplot
        if range_result =='yes':
            delta = 0.02
            range_min = merge_MinMax["min"].min() - 0.04
            range_max = merge_MinMax["max"].max() + 0.04
            
            fig.update_yaxes(range=[range_min, range_max], row=nb_listAllComb)
        '''


            


        dfTempComb = df[df["Combination"] == Which_channel]



        
        for i in range(len(date1)-1):
            dfTempComb = dfTempComb.explode(table_column_param)
            dfTempComb[table_column_param] = dfTempComb[table_column_param].astype('float')

            TempDF_1 = dfTempComb[dfTempComb["Date"] == date1[i]]
            TempDF_2 = dfTempComb[dfTempComb["Date"] == date2[i + 1]]



            X = date2[i + 1]
            Y = TempDF_Med[TempDF_Med["Date"]==X]
            Y = Y[ttest_table_column]
            t, p = stats.ttest_ind(TempDF_1[table_column_param], TempDF_2[table_column_param], equal_var=False)

            if p >= 0.05:
                symbol = '<sup><sup><b>ns</b></sup></sup>'
                sz = 30
            elif p >= 0.01: 
                symbol = '<sup><b>*</b></sup>'
                sz = 20
            elif p >= 0.001:
                symbol = '<sup><b>**</b></sup>'
                sz = 20
            else:
                symbol = '<sup><b>***</b></sup>'
                sz = 20

            fig.add_annotation(dict(font=dict(size=sz), 
                                    x=X, y=float(Y),
                                    text=symbol,
                                    showarrow=False,
                                    arrowhead=1,
                                    xref='x1',
                                    yref='y' + str(nb_listAllComb)))
            
        nb_listAllComb -= 1
    
    
    fig.show()
    
    if result == 'yes':
        global XYZpdf_name
        param = param.replace(" ", "_")
        param = param.replace(".", "")
        param = param.replace("/", "_")
        XYZpdf_name = f'{param}_boxplot.pdf'
        XYZpdf_path = os.path.join(im_path, XYZpdf_name)
        fig.write_image(XYZpdf_path)
    







def display_selected_plot(values, selected_param, df, df_MedStd, folder_selected, leg_dict, list_comb, date_list):
    main = tk.Tk()
    main.withdraw()
    main.geometry("100x100")



    result = tk.messagebox.askquestion("Save", "Do you want to save your figures in PDF format ?")


    if result == 'yes':
        im_path = os.path.join(folder_selected, "pdf_result")

        if not os.path.exists(im_path):
            os.makedirs(im_path)
    else:
        im_path = None

    sys_name = df["Microscope"].unique()

    index = 0
    DC_var = {}
    for a in range(len(list_comb)):
        index += 1
        DC_var["Comb" + str(index)] = df_MedStd.loc[df_MedStd['Combination'] == list_comb[a]].reset_index(drop=True)
    
    for i in selected_param:
        if i in values:
            param = i
            if param == 'Distances (µm)':
                table_column_param = param
                med_column_param = "Distances Median"
                ttest_table_column = 'Distances Max'

                
            else:
                table_column_param = param
                med_column_param = "Ratios Median"
                ttest_table_column = 'Ratios Max'



            create_box(df, param, table_column_param, med_column_param, im_path,
                           result, ttest_table_column, leg_dict, sys_name, 
                           DC_var, df_MedStd, date_list)
            
            print('\n')

    if result == 'yes':
        root = tk.Tk()
        root.withdraw()

        output_selected = fd.askdirectory(title='Select the output folder')

        pdfs = os.listdir(im_path)
        merger = PdfFileMerger()

        for pdf in pdfs:
            p = os.path.join(im_path, pdf)
            merger.append(p)

        fnew = f"{datetime.datetime.today().strftime('%Y%m%d')}_PLOT_RESULT.pdf"
        final_pdf = os.path.join(output_selected, fnew)
        counter = 0
        root, ext = os.path.splitext(fnew)
        while os.path.exists(f'{final_pdf}'):
            counter += 1
            fnew = '%s_(%i)%s' % (root, counter, ext)    
            final_pdf = os.path.join(output_selected, fnew)

        merger.write(final_pdf)
        merger.close()

        if output_selected == '':
            os.remove(fnew)
            print(f'No PDF file created !')
        else:
            print(f'{fnew} is created')
            print(f'PATH : {output_selected}')


        
        im_path = pathlib.Path(im_path)
        if im_path.exists() and im_path.is_dir():
            shutil.rmtree(im_path)



    else:
        print("No saving")
    