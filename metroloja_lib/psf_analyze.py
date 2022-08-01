import os, glob, pathlib, time, datetime, shutil
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
    with alive_bar(len_tot_image, force_tty = True) as bar:
        dtm = pd.DataFrame()
        dtm_sbr = pd.DataFrame()
        idx = 0
        for process in all_processed_path:
            # r=root, d=directories, f = files
            for r, d, f in os.walk(process):
                for file in f:
                    for dt in range(len(all_image_name)):
                        TempDate = all_image_name[dt]
                        for i in range(len(TempDate)):
                            grp = TempDate[i]
                            path_split = process.split(os.sep)

                            filename = grp
                            initTempDate = path_split[-3]
                            date = datetime.datetime.strptime(initTempDate, '%Y%m%d').date()
                            microscope = f'{path_split[-6]} : {path_split[-5]}'
                            for fn in lf_name:
                                if fn in grp:
                                    fn2 = fn.replace(' ','')
                                    if file.endswith("_summary.xls") and file.startswith(fn2):
                                        f_path = os.path.join(r, file)
                                        #fullpath = os.path.abspath(f_path)
                                        data = pd.read_csv(f_path, delimiter = "\t", index_col = False, header= 0)
                                        data = data.iloc[:, :-1] # Drop the last column

                                        # Find "Channel" indexe(s)
                                        q = "Dimension"
                                        c = data.columns[0]

                                        irow = data.query(f'"{q}" in {c}').index


                                        # Split dataframe and take Dimension's part
                                        last_check = 0
                                        dfs = []
                                        for ind in [irow[0], len(data)]:
                                            dfs.append(data.loc[last_check:ind-1])
                                            last_check = ind

                                        df_dimension = dfs[1]

                                        # Take SBR part
                                        df_dimension_SBR = dfs[0]
                                        #Select data column
                                        sbr = df_dimension_SBR.iloc[:,1]

                                        # Reindex column name
                                        df_dimension.columns = df_dimension.iloc[0]
                                        df_dimension = df_dimension.reindex(df_dimension.index.drop(1)).reset_index(drop=True)
                                        df_dimension.columns.name = None

                                        # Reindex row name
                                        df_dimension = df_dimension.set_index('Dimension')


                                        # Create XYZ dataframe
                                        x_FWHM = df_dimension.loc["Measured FWHM (µm)","X"]
                                        y_FWHM = df_dimension.loc["Measured FWHM (µm)","Y"]
                                        z_FWHM = df_dimension.loc["Measured FWHM (µm)","Z"]


                                        x_R2 = df_dimension.loc["Fit Goodness","X"]
                                        y_R2 = df_dimension.loc["Fit Goodness","Y"]
                                        z_R2 = df_dimension.loc["Fit Goodness","Z"]

                                        x_ratio = df_dimension.loc["Mes./theory ratio","X"]
                                        y_ratio = df_dimension.loc["Mes./theory ratio","Y"]
                                        z_ratio = df_dimension.loc["Mes./theory ratio","Z"]


                                        wavelenght = sbr.name[14:22]



                                        image_path = os.path.join(folder_selected, str(date), filename)
                                        TempList = pd.DataFrame({'Date':[date], 'Image Path':[image_path], "Microscope":[microscope], "Wavelength":[wavelenght], "Fit (R2)":[x_R2], 'Resolution (µm) : FWHM':[x_FWHM], 'Mes./theory resolution ratio (µm)':[x_ratio], 'Axe':"X"})
                                        dtm = pd.concat([dtm,TempList])

                                        TempList = pd.DataFrame({'Date':[date], 'Image Path':[image_path], "Microscope":[microscope], "Wavelength":[wavelenght], "Fit (R2)":[y_R2], 'Resolution (µm) : FWHM':[y_FWHM], 'Mes./theory resolution ratio (µm)':[y_ratio], 'Axe':"Y"})
                                        dtm = pd.concat([dtm,TempList])

                                        TempList = pd.DataFrame({'Date':[date], 'Image Path':[image_path], "Microscope":[microscope], "Wavelength":[wavelenght], "Fit (R2)":[z_R2], 'Resolution (µm) : FWHM':[z_FWHM], 'Mes./theory resolution ratio (µm)':[z_ratio], 'Axe':"Z"})
                                        dtm = pd.concat([dtm,TempList])


                                        #Create SBR dataframe
                                        TempList = pd.DataFrame({'Date':[date], 'Image Path':[image_path], "Microscope":[microscope], "Wavelength":[wavelenght], 'Sig/Backgnd ratio':[sbr[0]]})
                                        dtm_sbr = pd.concat([dtm_sbr,TempList])

                                        time.sleep(.005)
                                        bar()

    dtm.reset_index(drop=True, inplace=True)
    dtm_sbr.reset_index(drop=True, inplace=True)
    df_XYZ = dtm
    df_SBR = dtm_sbr
    
    return(df_XYZ, df_SBR)

    

    
def XYZ_stats(df_XYZ):
    df_XYZ = df_XYZ.explode('Fit (R2)')
    df_XYZ['Fit (R2)'] = df_XYZ['Fit (R2)'].astype('float')

    median_df_R2 = df_XYZ.groupby(['Date', 'Microscope', 'Wavelength', 'Axe'])['Fit (R2)'].median().to_frame('R2 median').reset_index()
    mean_df_R2 = df_XYZ.groupby(['Date', 'Microscope', 'Wavelength', 'Axe'])['Fit (R2)'].mean().to_frame('R2 mean').reset_index()
    std_df_R2 = df_XYZ.groupby(['Date', 'Microscope', 'Wavelength', 'Axe'])['Fit (R2)'].std().to_frame('R2 std').reset_index()
    max_df_R2 = df_XYZ.groupby(['Date', 'Microscope', 'Wavelength', 'Axe'])['Fit (R2)'].max().to_frame('R2 max').reset_index()



    df_XYZ = df_XYZ.explode('Resolution (µm) : FWHM')
    df_XYZ['Resolution (µm) : FWHM'] = df_XYZ['Resolution (µm) : FWHM'].astype('float')

    median_df_FWHM = df_XYZ.groupby(['Date', 'Microscope', 'Wavelength', 'Axe'])['Resolution (µm) : FWHM'].median().to_frame('FWHM median').reset_index()
    mean_df_FWHM = df_XYZ.groupby(['Date', 'Microscope', 'Wavelength', 'Axe'])['Resolution (µm) : FWHM'].mean().to_frame('FWHM mean').reset_index()
    std_df_FWHM = df_XYZ.groupby(['Date', 'Microscope', 'Wavelength', 'Axe'])['Resolution (µm) : FWHM'].std().to_frame('FWHM std').reset_index()
    max_df_FWHM = df_XYZ.groupby(['Date', 'Microscope', 'Wavelength', 'Axe'])['Resolution (µm) : FWHM'].max().to_frame('FWHM max').reset_index()



    df_XYZ = df_XYZ.explode('Mes./theory resolution ratio (µm)')
    df_XYZ['Mes./theory resolution ratio (µm)'] = df_XYZ['Mes./theory resolution ratio (µm)'].astype('float')

    median_df_ratio = df_XYZ.groupby(['Date', 'Microscope', 'Wavelength', 'Axe'])['Mes./theory resolution ratio (µm)'].median().to_frame('Mes./theory resolution ratio median').reset_index()
    mean_df_ratio = df_XYZ.groupby(['Date', 'Microscope', 'Wavelength', 'Axe'])['Mes./theory resolution ratio (µm)'].mean().to_frame('Mes./theory resolution ratio mean').reset_index()
    std_df_ratio = df_XYZ.groupby(['Date', 'Microscope', 'Wavelength', 'Axe'])['Mes./theory resolution ratio (µm)'].std().to_frame('Mes./theory resolution ratio std').reset_index()
    max_df_ratio = df_XYZ.groupby(['Date', 'Microscope', 'Wavelength', 'Axe'])['Mes./theory resolution ratio (µm)'].max().to_frame('Mes./theory resolution ratio max').reset_index()



    allDFstat = [median_df_R2, mean_df_R2, std_df_R2, max_df_R2, median_df_FWHM, mean_df_FWHM, std_df_FWHM, max_df_FWHM, median_df_ratio, mean_df_ratio, std_df_ratio, max_df_ratio]
    dfXYZ_MedStd = reduce(lambda  left,right: pd.merge(left,right,on=['Date', 'Microscope', 'Wavelength', 'Axe'], how='outer'), allDFstat)



    return(dfXYZ_MedStd)




def SBR_stats(df_SBR):
    df_SBR = df_SBR.explode('Sig/Backgnd ratio')
    df_SBR['Sig/Backgnd ratio'] = df_SBR['Sig/Backgnd ratio'].astype('float')

    median_df_SBR = df_SBR.groupby(['Date', 'Microscope', 'Wavelength'])['Sig/Backgnd ratio'].median().to_frame('Median').reset_index()
    mean_df_SBR = df_SBR.groupby(['Date', 'Microscope', 'Wavelength'])['Sig/Backgnd ratio'].mean().to_frame('Mean').reset_index()
    std_df_SBR  = df_SBR.groupby(['Date', 'Microscope', 'Wavelength'])['Sig/Backgnd ratio'].std().to_frame('Std').reset_index()
    eff_df_SBR  = df_SBR.groupby(['Date', 'Microscope', 'Wavelength']).size().reset_index(name='n')
    max_df_SBR  = df_SBR.groupby(['Date', 'Microscope', 'Wavelength'])['Sig/Backgnd ratio'].max().to_frame('Max').reset_index()


    allSBRstat = [median_df_SBR, mean_df_SBR, std_df_SBR, eff_df_SBR, max_df_SBR]
    df_MedStd_SBR = reduce(lambda  left,right: pd.merge(left,right,on=['Date', 'Microscope', 'Wavelength'], how='outer'), allSBRstat)

    leg_dict = {}
    for i in range(len(df_MedStd_SBR)):
        t = df_MedStd_SBR['Date'].iloc[i]
        leg_dict[str(t)] = str(t) + ' (n = ' + str(df_MedStd_SBR['n'].iloc[i]) + ')'

    return(df_MedStd_SBR, leg_dict)
    




def create_XYZ_box(df_XYZ, param, table_column_param, med_column_param, im_path,
                   result, ttest_table_column, df_MedStd_SBR, leg_dict, sys_name, 
                   dfX_MedStd, dfY_MedStd, dfZ_MedStd):
    date1 = df_MedStd_SBR["Date"].tolist()
    date2 = date1.copy()
    date2[0] = "first date"
    
    df_XYZ = df_XYZ.explode(table_column_param)
    df_XYZ[table_column_param] = df_XYZ[table_column_param].astype('float')
    

    fig = px.box(df_XYZ, x = "Date", y = table_column_param, color = "Date", category_orders={"Date" : date1},
                 facet_row="Axe", title = f"{sys_name[0]}           {param} Box plot           PICT-BDD           (Update : {datetime.datetime.today().strftime('%Y-%m-%d')})<br><sub><b>Statistical T-Tests are carried out between a date and the date immediately preceding it</b></sub>", points="outliers", height=1000, width=900).update_yaxes(matches=None)

    fig.update_layout(showlegend=True)
    fig.update_layout(title_x=0.5)
    
    
    
    fig.for_each_trace(lambda t: t.update(name = leg_dict[t.name],
                                          legendgroup = leg_dict[t.name],
                                          hovertemplate = t.hovertemplate.replace(t.name, leg_dict[t.name])
                                         )
                      )



    fig.add_trace(
        go.Scatter(x=dfX_MedStd["Date"].tolist(), y=dfX_MedStd[med_column_param].tolist(), showlegend=False, mode='lines+markers', line=dict(color="#000000")), row=3, col=1
    )
    fig.add_trace(
        go.Scatter(x=dfY_MedStd["Date"].tolist(), y=dfY_MedStd[med_column_param].tolist(), showlegend=False, mode='lines+markers', line=dict(color="#000000")), row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=dfZ_MedStd["Date"].tolist(), y=dfZ_MedStd[med_column_param].tolist(), showlegend=False, mode='lines+markers', line=dict(color="#000000")), row=1, col=1
    )



    dfXY = df_XYZ[(df_XYZ["Axe"] == "X") | (df_XYZ["Axe"] == "Y")]

    max_df_FWHM = dfXY.groupby(['Date', 'Microscope', 'Wavelength', 'Axe'])[table_column_param].max().to_frame('max').reset_index()
    min_df_FWHM = dfXY.groupby(['Date', 'Microscope', 'Wavelength', 'Axe'])[table_column_param].min().to_frame('min').reset_index()

    merge_MinMax_FWHM = pd.merge(min_df_FWHM, max_df_FWHM, how='left', on=['Date', 'Microscope', 'Wavelength', 'Axe'])


    # Select XY range for boxplot
    range_min_FWHM = merge_MinMax_FWHM["min"].min() - 0.02
    range_max_FWHM = merge_MinMax_FWHM["max"].max() + 0.02


    fig.update_yaxes(range=[range_min_FWHM, range_max_FWHM], row=2)
    fig.update_yaxes(range=[range_min_FWHM, range_max_FWHM], row=3)
    
    
    
    

    dfX = df_XYZ[df_XYZ["Axe"] == "X"]
    dfY = df_XYZ[df_XYZ["Axe"] == "Y"]
    dfZ = df_XYZ[df_XYZ["Axe"] == "Z"]
    

        

    for i in range(len(date1)-1):
        dfX = dfX.explode(table_column_param)
        dfX[table_column_param] = dfX[table_column_param].astype('float')
        
        TempDF_X1 = dfX[dfX["Date"] == date1[i]]
        TempDF_X2 = dfX[dfX["Date"] == date2[i + 1]]

        X = date2[i + 1]
        Yx = dfX_MedStd[dfX_MedStd["Date"]==X]
        Yx = Yx[ttest_table_column]
        tX, pX = stats.ttest_ind(TempDF_X1[table_column_param], TempDF_X2[table_column_param], equal_var=False)
        
        if pX >= 0.05:
            symbolX = '<sup><sup><b>ns</b></sup></sup>'
            sz = 30
        elif pX >= 0.01: 
            symbolX = '<sup><b>*</b></sup>'
            sz = 20
        elif pX >= 0.001:
            symbolX = '<sup><b>**</b></sup>'
            sz = 20
        else:
            symbolX = '<sup><b>***</b></sup>'
            sz = 20
        fig.add_annotation(dict(font=dict(size=sz), 
                                x=X, y=float(Yx),
                                text=symbolX,
                                showarrow=False,
                                arrowhead=1,
                                xref='x1',
                                yref='y3'))



        dfY = dfY.explode(table_column_param)
        dfY[table_column_param] = dfY[table_column_param].astype('float')
        
        TempDF_Y1 = dfY[dfY["Date"] == date1[i]]
        TempDF_Y2 = dfY[dfY["Date"] == date2[i + 1]]

        Yy = dfY_MedStd[dfY_MedStd["Date"]==X]
        Yy = Yy[ttest_table_column]
        tY, pY = stats.ttest_ind(TempDF_Y1[table_column_param], TempDF_Y2[table_column_param], equal_var=False)
        
        if pY >= 0.05:
            symbolY = '<sup><sup><b>ns</b></sup></sup>'
            sz = 30
        elif pY >= 0.01: 
            symbolY = '<sup><b>*</b></sup>'
            sz = 20
        elif pY >= 0.001:
            symbolY = '<sup><b>**</b></sup>'
            sz = 20
        else:
            symbolY = '<sup><b>***</b></sup>'
            sz = 20
        
        fig.add_annotation(dict(font=dict(size=sz), 
                                x=X, y=float(Yy),
                                text=symbolY,
                                showarrow=False,
                                arrowhead=1,
                                xref='x1',
                                yref='y2'))



        dfZ = dfZ.explode(table_column_param)
        dfZ[table_column_param] = dfZ[table_column_param].astype('float')
        
        TempDF_Z1 = dfZ[dfZ["Date"] == date1[i]]
        TempDF_Z2 = dfZ[dfZ["Date"] == date2[i + 1]]

        Yz = dfZ_MedStd[dfZ_MedStd["Date"]==X]
        Yz = Yz[ttest_table_column]
        tZ, pZ = stats.ttest_ind(TempDF_Z1[table_column_param], TempDF_Z2[table_column_param], equal_var=False)
        
        if pZ >= 0.05:
            symbolZ = '<sup><sup><b>ns</b></sup></sup>'
            sz = 30
        elif pZ >= 0.01: 
            symbolZ = '<sup><b>*</b></sup>'
            sz = 20
        elif pZ >= 0.001:
            symbolZ = '<sup><b>**</b></sup>'
            sz = 20
        else:
            symbolZ = '<sup><b>***</b></sup>'
            sz = 20
        
        
        fig.add_annotation(dict(font=dict(size=sz), 
                                x=X, y=float(Yz),
                                text=symbolZ,
                                showarrow=False,
                                arrowhead=1,
                                xref='x1',
                                yref='y1'))
    
    

    fig.show()
    
    if result == 'yes':
        global XYZpdf_name
        param = param.replace(" ", "_")
        param = param.replace(".", "")
        param = param.replace("/", "_")
        XYZpdf_name = f'{param}_boxplot.pdf'
        XYZpdf_path = os.path.join(im_path, XYZpdf_name)
        fig.write_image(XYZpdf_path)
    




def create_SBR_box(df_SBR, result, im_path, df_MedStd_SBR, leg_dict, sys_name):
    date1 = df_MedStd_SBR["Date"].tolist()
    date2 = date1.copy()
    date2[0] = "first date"
    
    df_SBR = df_SBR.explode("Sig/Backgnd ratio")
    df_SBR["Sig/Backgnd ratio"] = df_SBR["Sig/Backgnd ratio"].astype('float')
    
    
    fig = px.box(df_SBR, x = "Date", y = "Sig/Backgnd ratio", color = "Date", category_orders={"Date" : date1},
                 title = f"{sys_name[0]}           Sig/Backgnd ratio Box plot           PICT-BDD           (Update : {datetime.datetime.today().strftime('%Y-%m-%d')})<br><sub><b>Statistical T-Tests are carried out between a date and the date immediately preceding it</b>", points="outliers", height=1000, width=900).update_yaxes(matches=None)

    fig.update_layout(showlegend=True)
    fig.for_each_trace(lambda t: t.update(name = leg_dict[t.name],
                                          legendgroup = leg_dict[t.name],
                                          hovertemplate = t.hovertemplate.replace(t.name, leg_dict[t.name])
                                         )
                      )
    
    fig.add_trace(
        go.Scatter(x=df_MedStd_SBR["Date"].tolist(), y=df_MedStd_SBR["Median"].tolist(), showlegend=False, mode='lines+markers', line=dict(color="#000000"))
    )
    fig.update_layout(title_x=0.5)
    
    


    for i in range(len(date1)-1):
        
        TempDF_SBR1 = df_SBR[df_SBR["Date"] == date1[i]]
        TempDF_SBR2 = df_SBR[df_SBR["Date"] == date2[i + 1]]

        X = date2[i + 1]
        Y = df_MedStd_SBR[df_MedStd_SBR["Date"]==X]
        Y = Y["Max"]
        t, p = stats.ttest_ind(TempDF_SBR1["Sig/Backgnd ratio"], TempDF_SBR2["Sig/Backgnd ratio"], equal_var=False)
        
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
                                arrowhead=1))

    
    fig.show()
    
    if result == 'yes':
        global SBRpdf_name
        SBRpdf_name = f'SBR_boxplot.pdf'
        SBRpdf_path = os.path.join(im_path, SBRpdf_name)
        fig.write_image(SBRpdf_path)



def select_param():
    values = {"FWHM" : "1",
              "Fit (R2)" : "2",
              "Mes./theory resolution ratio" : "3",
              "SBR" : "4"}


    master2 = tk.Tk()
    master2.geometry("450x150")
    master2.title('Check all the measurements you want to plot')


    values2 = ["FWHM", "Fit (R2)", "Mes./theory resolution ratio", "SBR"]

    states_list = []
    for text in values2:
        check = tk.StringVar(master2)
        check_but = tk.Checkbutton(master2, text = text, variable = check,
                                   onvalue = text, offvalue = 'off', command=check.get())
        check_but.pack(padx=0.5, pady=0.5, anchor=tk.W)
        states_list.append(check)

    button2 = tk.Button(
        master2,
        text="Get Selected",
        command=master2.quit)
    button2.pack(fill=tk.X, padx=5, pady=5)

    btn = tk.Button(master2,text="Close", command=master2.quit)
    btn.pack(pady = 5)


    master2.mainloop()
    master2.destroy()

    print("Selection :")
    selected_param = []
    for v in states_list:
        if v.get()!='':
            selected_param.append(v.get())
            print(f"  * {v.get()}")
    print('OK !')

    return(selected_param, values)


    
    

def display_selected_plot(values, selected_param, df_XYZ, df_SBR, dfXYZ_MedStd, df_MedStd_SBR, folder_selected, leg_dict):
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


    sys_name = df_XYZ["Microscope"].unique()

    dfX_MedStd = dfXYZ_MedStd.loc[dfXYZ_MedStd['Axe'] == 'X']
    dfY_MedStd = dfXYZ_MedStd.loc[dfXYZ_MedStd['Axe'] == 'Y']
    dfZ_MedStd = dfXYZ_MedStd.loc[dfXYZ_MedStd['Axe'] == 'Z']


    for i in selected_param:
        if i in values:
            param = i
            if int(values[i]) in range(1, 4):
                if param == 'FWHM':
                    table_column_param = 'Resolution (µm) : FWHM'
                    med_column_param = "FWHM median"
                    ttest_table_column = 'FWHM max'

                elif param == 'Fit (R2)':
                    table_column_param = 'Fit (R2)'
                    med_column_param = "R2 median"
                    ttest_table_column = 'R2 max'


                elif param == 'Mes./theory resolution ratio':
                    table_column_param = 'Mes./theory resolution ratio (µm)'
                    med_column_param = "Mes./theory resolution ratio median"
                    ttest_table_column = 'Mes./theory resolution ratio max'

                create_XYZ_box(df_XYZ, param, table_column_param, med_column_param, im_path,
                               result, ttest_table_column, df_MedStd_SBR, leg_dict, sys_name, 
                               dfX_MedStd, dfY_MedStd, dfZ_MedStd)
            if int(values[i]) == 4:
                create_SBR_box(df_SBR, result, im_path, df_MedStd_SBR, leg_dict, sys_name)
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
    
