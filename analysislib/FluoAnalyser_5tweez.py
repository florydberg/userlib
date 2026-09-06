from lyse import *
from runmanager.remote import *
from pylab import *
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec
from labscript.labscript import *
import analysislib
from scipy.optimize import curve_fit, least_squares
import time # for testing speed of program
import datetime, time
ts=time.time()
datetime.datetime.now()
dt=datetime.datetime.now().date()

if True: #functions definition
    if True:  # Constants and Image Analysis  
        pixel_size = 4.6e-6  # meters per pixel (Orca magnified)
        effective_pixel_size = 1.127e-6 # M = f_tubelens/f_eff; pixel_eff = pixel_size/M, ftubelens = 100, f_eff = 24.5mm
 
    def gaussian_2d(xy, amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
        theta = theta * np.pi*0
        x, y = xy
        xo = float(xo)
        yo = float(yo)
        a = (np.cos(theta)**2) / (2 * sigma_x**2) + (np.sin(theta)**2) / (2 * sigma_y**2)
        b = -(np.sin(2 * theta)) / (4 * sigma_x**2) + (np.sin(2 * theta)) / (4 * sigma_y**2)
        c = (np.sin(theta)**2) / (2 * sigma_x**2) + (np.cos(theta)**2) / (2 * sigma_y**2)
        return amplitude * np.exp(-(a * (x - xo)**2 + 2 * b * (x - xo) * (y - yo) + c * (y - yo)**2)) + offset
                   
    def saving_script(path):
        with Run(path).open('r+') as shot:
            data_frame = data()
            # path=data_frame['filepath'].iloc[-1]
            file_path = os.path.realpath(__file__)
            prefix = os.path.dirname(analysislib.__file__)
            save_path = 'analysislib/' + file_path.replace(prefix, '').replace('\\', '/').replace('//', '/')
            with h5py.File(path, 'r') as hdf5_file:
                        if save_path not in hdf5_file:
                            # Don't try to save the same module script twice! (seems to at least
                            # double count __init__.py when you import an entire module as in
                            # from labscriptlib.stages import * where stages is a folder with an
                            # __init__.py file. Doesn't seem to want to double count files if
                            # you just import the contents of a file within a module
                            hdf5_file.create_dataset(save_path, data=open(file_path).read()) #TODO: fix the recreation of group in dataframe

            _vcs_cache_rlock = threading.RLock()
            def _file_watcher_callback(name, info, event):
                with _vcs_cache_rlock:
                    _vcs_cache[name] = _run_vcs_commands(name)
                _file_watcher = FileWatcher(_file_watcher_callback)
                with _vcs_cache_rlock:
                    if not path in _vcs_cache:
                        # Add file to watch list and create its entry in the cache.
                        _file_watcher.add_file(path)
                        _file_watcher_callback(path, None, None)

    def save_imag(plt, name):
        picname = name
        tm = datetime.datetime.now()
        img_name=str(dt) + '_' + tm.strftime("%H") + tm.strftime("%M") + tm.strftime("%S") + '_' +tm.strftime("%f")
        print(path)
        one_level_up = os.path.dirname(path)
        plt.savefig(one_level_up + '/' + img_name +  '_' + picname + ".png")
        print(picname + ' saved')

    def MotPlot(MotSpot, rmin = None, rmax = None, GaussFit=False):
        MOTray=round(size(MotSpot,1)/2)
        print(MOTray)
        if rmin == None:
            rmin=np.amin(MotSpot)
        if rmax == None:
            rmax=np.amax(MotSpot)
        plt.figure(figsize=(10, 10))
        plt.rcParams.update({'font.size': 14})
        h, w = MotSpot.shape 
        h = h * 2
        w = w * 2
        if GaussFit:
            x = np.linspace(1, MOTray*2, MOTray*2)
            y = np.linspace(1, MOTray*2, MOTray*2)
            xx, yy = np.meshgrid(x, y)
            X = xx.ravel(order='F')
            Y = yy.ravel(order='F')
            initial_guess = (260, MOTray, MOTray, MOTray/2, MOTray/2, 0.01, 0.01)
            try:
                popt, cov = curve_fit(gaussian_2d, (X, Y), MotSpot.ravel(order='F'), p0=initial_guess)
            except:
                popt = [26, 1, 1, 1, 1, 0, 0]
    
            amplitude, xo, yo, sigma_x, sigma_y, theta, offset = popt
            popt=amplitude, xo, yo, sigma_x, sigma_y, theta, offset  

            fit_data = gaussian_2d((X, Y), *popt)
            fitdata = fit_data.reshape((MOTray*2, MOTray*2), order='F')
            gauy = np.sum(fitdata, axis=1)
            gaux = np.sum(fitdata, axis=0)
        intx = np.sum(MotSpot, axis=0)
        inty = np.sum(MotSpot, axis=1)
        
        n_ticks=7
        # x_values=np.round(linspace(0,(MotSpot.shape[0])*pixel_size*1000*(n_ticks-1)/n_ticks, n_ticks),2) 
        x_values=np.round(linspace(0,(MotSpot.shape[0])*effective_pixel_size*1e6*(n_ticks-1)/n_ticks, n_ticks),2)
        x_ticks=np.arange(0, MotSpot.shape[0], MotSpot.shape[0]/n_ticks)
        # y_values=np.round(linspace(0,(MotSpot.shape[0])*pixel_size*1000*(n_ticks-1)/n_ticks, n_ticks),2)
        y_values=np.round(linspace(0,(MotSpot.shape[0])*effective_pixel_size*1e6*(n_ticks-1)/n_ticks, n_ticks),2)
        y_ticks=np.arange(0, MotSpot.shape[1], MotSpot.shape[0]/n_ticks)

        gs = gridspec.GridSpec(2, 2, width_ratios=[w * .2, w], height_ratios=[ h, h * .2])
        ax = [plt.subplot(gs[3]), plt.subplot(gs[0]), plt.subplot(gs[1])]
        ax[0].plot(intx, 'b')  
        if GaussFit:     
            ax[0].plot(np.linspace(1, intx.shape, MOTray*2)*effective_pixel_size, gaux,  'r')       
        ax[1].plot(inty[::-1], np.linspace(1, inty.shape, MOTray*2), 'b') 
        if GaussFit:
            pixel_line=np.linspace(1, inty.shape, MOTray*2)*effective_pixel_size
            ax[1].plot(gauy[::-1], pixel_line, 'r') 
        ax[2].imshow(MotSpot, cmap='plasma',vmin=rmin, vmax=rmax) 
        plt.rcParams.update({'font.size': 20})
        plt.title('Mot Spot')
        # if not GaussFit:
        #     # plt.gca().add_patch(back)
        plt.gca().add_patch(TweezArea3)
        plt.gca().add_patch(TweezArea2)
        plt.gca().add_patch(TweezArea1)
        if saving_plots: save_imag(plt, 'mot_fluo')
        if True:
            plt.xticks(ticks=x_ticks, labels=x_values)
            plt.yticks(ticks=y_ticks, labels=y_values)
            plt.xlabel('um')
            plt.ylabel('um')
        if GaussFit:
            x_0=round(xo*effective_pixel_size)
            y_0=round(yo*effective_pixel_size)
            std_dev=(sigma_x+sigma_y)/2*effective_pixel_size
            # plt.colorbar(MotSpot)
            plt.xlabel("peak = %d , waist = %d, center = %a um" %(round(amplitude), std_dev, [x_0,y_0]))
            shot.save_result('peak_RedMot', amplitude)
            shot.save_result('waist_RedMot', std_dev)
            shot.save_result('center_RedMot', [x_0,y_0])
            shot.save_result('angle_RedMot', theta)
            shot.save_result('offset_RedMot', offset)
        plt.tight_layout()
        plt.show() 

    def TweezerAnalysis(TweezerSpot, ii, plotting=False, GaussFit=False):
        h, w = TweezerSpot.shape 
        h = h * 2
        w = w * 2
        # print(ii)
        # print(TweezerSpot)
        
        conversion_counts_to_electron = 0.11
        quantum_efficiency = 0.85

        TweezerPoint=TweezerSpot[Tray-waist:Tray+waist, Tray-waist:Tray+waist]*conversion_counts_to_electron/quantum_efficiency
        mean_count=mean(TweezerPoint)
        photon_count=sum(TweezerPoint)
        var_count=var(TweezerPoint)
        max_count=np.max(TweezerPoint)
        shot.save_result('mean_tweezer_'+str(ii), mean_count)
        shot.save_result('max_tweezer_'+str(ii), max_count)
        shot.save_result('variance_tweezer_'+str(ii), var_count)
        shot.save_result('photon_tweezer_'+str(ii), photon_count)
        shot.save_result('atom_in_tweezer_'+str(ii), int(photon_count>atom_presence_threshold))




        if GaussFit:
            x = np.linspace(1, Tray*2, Tray*2)
            y = np.linspace(1, Tray*2, Tray*2)
            xx, yy = np.meshgrid(x, y)
            X = xx.ravel(order='F')
            Y = yy.ravel(order='F')
            initial_guess = (260, Tray, Tray, Tray/2, Tray/2, 0.01, 0.01)
            try:
                popt, _ = curve_fit(gaussian_2d, (X, Y), TweezerSpot.ravel(order='F'), p0=initial_guess)
            except:
                popt = [26, 1, 1, 1, 1, 0, 0]
    
            amplitude, xo, yo, sigma_x, sigma_y, theta, offset = popt
            popt=amplitude, xo, yo, sigma_x, sigma_y, theta, offset  
            std_dev=(sigma_x+sigma_y)/2
            fit_data = gaussian_2d((X, Y), *popt)
            fitdata = fit_data.reshape((Tray*2, Tray*2), order='F')
            gauy = np.sum(fitdata, axis=1)
            gaux = np.sum(fitdata, axis=0)
            shot.save_result('peak_tweezer_'+str(ii), amplitude)
            shot.save_result('deviation_tweezer_'+str(ii), std_dev)

        if plotting:
            plt.figure(figsize=(10, 10))

            gs = gridspec.GridSpec(2, 2, width_ratios=[w * .2, w], height_ratios=[ h, h * .2])
            ax = [plt.subplot(gs[3]), plt.subplot(gs[0]), plt.subplot(gs[1])]
            ax[2].imshow(TweezerSpot, cmap='plasma',vmin=0 , vmax=50)
            plt.title('Tweezer '+ str(ii) + ' Spot')
            intx = np.sum(TweezerSpot, axis=0)
            inty = np.sum(TweezerSpot, axis=1)
            ax[0].plot(intx, 'b')
            ax[1].plot(inty[::-1], np.linspace(1, inty.shape, Tray*2), 'b') 
            x_label1="mean = %d , variance = %d" %(round(mean_count), var_count)

            TweezArea=patches.Rectangle([Tray-waist,Tray-waist], tweezROI, tweezROI, linewidth=1, edgecolor='r', facecolor='none')

            plt.gca().add_patch(TweezArea)
            plt.legend(['Tweezer Integration Area'], loc ="lower right")
            x_label2=''
            if GaussFit:
                x_label2=", peak = %d , std_dev = %d " %(round(amplitude), std_dev)
                ax[0].plot(gaux, 'r')
                ax[1].plot(gauy[::-1], np.linspace(1, inty.shape, Tray*2), 'r')
            plt.xlabel(x_label1+x_label2)
            plt.show() 
            if saving_plots: save_imag(plt, 'tweez_fluo_'+ str(ii))

######################
saving_plots=True
tweezROI=4
Tray=2
waist=round(tweezROI/2)
atom_presence_threshold=20
######################
plt.style.use("default")
print(path)
with Run(path).open('r+') as shot:
    start_time = time.time()
    data_frame=data(path)
    ROI = data_frame['Orca_ROI']

    second_shot = data_frame['second_shot']
    
    deltax=-1
    deltay=0
    # T1=[49+deltax,36+deltay]
    # T2=[55+deltax,36+deltay]
    # T3=[62+deltax,36+deltay]
    # T4=[49+deltax,42+deltay]
    # T5=[55+deltax,42+deltay]
    # T6=[62+deltax,42+deltay]
    # T7=[49+deltax,49+deltay]
    # T8=[55+deltax,49+deltay]
    # T9=[62+deltax,49+deltay]  

    T1=[47+deltax,36+deltay]
    T2=[54+deltax,36+deltay]
    T3=[60+deltax,36+deltay]
    T4=[47+deltax,43+deltay]
    T5=[54+deltax,43+deltay]
    T6=[60+deltax,43+deltay]
    T7=[47+deltax,49+deltay]
    T8=[54+deltax,49+deltay]
    T9=[60+deltax,49+deltay]  

    centers = [T1,T2,T3,T4,T5,T6,T7,T8,T9]


    img={}
    for i in ['TweezFluo']:    
        shot_image=shot.get_image('Orca_Camera',str(i),'frame')  # Obtaining multiple images and averaging them:
        if int(data_frame['n_loop'])>1: img[str(i)] = np.average(shot_image.astype(np.float32),axis=0)
        else: img[str(i)]=shot_image.astype(np.float32)
    FluoImag=img['TweezFluo']

    # plt.figure()
    # plt.imshow(FluoImag, cmap='plasma') #

    if second_shot:
        img={}
        for i in ['second-shot']:    
            shot_image=shot.get_image('Orca_Camera',str(i),'frame')  # Obtaining multiple images and averaging them:
            if int(data_frame['n_loop'])>1: img[str(i)] = np.average(shot_image.astype(np.float32),axis=0)
            else: img[str(i)]=shot_image.astype(np.float32)
        SecondImag=img['second-shot']
    
    # BGspot=FluoImag[0:tweezROI, 0:tweezROI]
    # if second_shot:
    #     BGspot_2nd=SecondImag[0:tweezROI, 0:tweezROI]

    #new BG calculation 

    roi_size = 5
    img_shape = FluoImag.shape
    mask = np.ones(img_shape, dtype=bool)

    for cx, cy in centers:
        x_min = max(cx-roi_size,0)
        x_max = min(cx+roi_size+1,img_shape[1])
        y_min = max(cy-roi_size,0)
        y_max = min(cy+roi_size+1,img_shape[0])
        mask[y_min:y_max, x_min:x_max] = False
    
    BGspot= FluoImag[mask]
    background_value = np.mean(BGspot)
    # BGspot_tosave = BGspot-background_value
    # background_value_tosave = np.mean(BGspot_tosave)
    # masked_image = np.ma.array(FluoImag, mask=~mask)  

    test_roi_center = (30, 30)
    test_roi_size = 1  

    cx_BG, cy_BG = test_roi_center
    x_min_BG = max(cx_BG - test_roi_size, 0)
    x_max_BG = min(cx_BG + test_roi_size + 1, img_shape[1])
    y_min_BG = max(cy_BG - test_roi_size, 0)
    y_max_BG = min(cy_BG + test_roi_size + 1, img_shape[0])
    
    test_roi = FluoImag[y_min_BG:y_max_BG, x_min_BG:x_max_BG]

    BGspot_tosave = test_roi - background_value
    background_value_tosave = np.mean(BGspot_tosave)
    print('ciao', background_value_tosave)

    # plt.imshow(FluoImag, cmap='viridis')
    # plt.gca().add_patch(plt.Rectangle((x_min_BG, y_min_BG), 3, 3, edgecolor='r', facecolor='none'))
    # plt.title("Immagine con ROI neutra evidenziata")
    # plt.show()

    # fig, ax = plt.subplots(figsize=(8, 6))
    # im = ax.imshow(masked_image, cmap='plasma')
    # ax.set_title("background mask (fist shot)")
    # plt.axis('off')
    # cbar = plt.colorbar(im, ax=ax)
    # plt.tight_layout()
    # plt.show()

    if second_shot:
        img_shape_2nd = SecondImag.shape
        mask_2nd = np.ones(img_shape_2nd, dtype=bool)

        for cx, cy in centers:
            x_min = max(cx - roi_size, 0)
            x_max = min(cx + roi_size + 1, img_shape_2nd[1])
            y_min = max(cy - roi_size, 0)
            y_max = min(cy + roi_size + 1, img_shape_2nd[0])
            mask_2nd[y_min:y_max, x_min:x_max] = False

        BGspot_2nd = SecondImag[mask_2nd]
        background_value_2nd = np.mean(BGspot_2nd)

        # BGspot_2nd_tosave = BGspot_2nd-background_value
        # background_value_2nd_tosave = np.mean(BGspot_2nd_tosave)
        test_roi_center_2nd = (30, 30)
        test_roi_size_2nd = 1  

        cx_BG_2nd, cy_BG_2nd = test_roi_center_2nd
        x_min_BG_2nd = max(cx_BG_2nd - test_roi_size_2nd, 0)
        x_max_BG_2nd = min(cx_BG_2nd + test_roi_size_2nd + 1, img_shape[1])
        y_min_BG_2nd = max(cy_BG_2nd - test_roi_size_2nd, 0)
        y_max_BG_2nd = min(cy_BG_2nd + test_roi_size_2nd + 1, img_shape[0])
        
        test_roi_2nd = FluoImag[y_min_BG_2nd:y_max_BG_2nd, x_min_BG_2nd:x_max_BG_2nd]

        BGspot_2nd_tosave = test_roi_2nd - background_value_2nd
        background_value_2nd_tosave = np.mean(BGspot_2nd_tosave)



    # MOTray=50*5
    MOTray=50
    
    if ROI=='full': #ROIS
        MOT0=[2360,841]  
        MOTArea=patches.Circle(MOT0, MOTray, linewidth=1, edgecolor='r', facecolor='none')
        MotSpot=FluoImag[MOT0[1]-MOTray:MOT0[1]+MOTray, MOT0[0]-MOTray:MOT0[0]+MOTray]-np.average(BGspot)
        # plt.gca().add_patch(MOTArea)
    elif ROI=='mot':
        # MOT0=[664,431] 
        # MOTArea=patches.Circle(MOT0, MOTray, linewidth=1, edgecolor='r', facecolor='none')
        # MotSpot=FluoImag[MOT0[1]-MOTray:MOT0[1]+MOTray, MOT0[0]-MOTray:MOT0[0]+MOTray]-background_value #np.average(BGspot)
        # if second_shot:
        #     MotSpot2nd=SecondImag[MOT0[1]-MOTray:MOT0[1]+MOTray, MOT0[0]-MOTray:MOT0[0]+MOTray]-background_value_2nd #np.average(BGspot_2nd)
        # plt.gca().add_patch(MOTArea)
            MOT0=[round(np.shape(FluoImag)[0]/2),round(np.shape(FluoImag)[1]/2)] 
            MOTArea=patches.Circle(MOT0, MOTray, linewidth=1, edgecolor='r', facecolor='none')
            MotSpot=FluoImag[MOT0[1]-MOTray:MOT0[1]+MOTray, MOT0[0]-MOTray:MOT0[0]+MOTray]
    elif ROI=='tweez':
        MOTArea=patches.Circle(MOTray, MOTray, linewidth=1, edgecolor='r', facecolor='none')
        MotSpot=FluoImag-background_value #np.average(BGspot)
        if second_shot:
            MotSpot2nd=SecondImag-background_value_2nd #np.average(BGspot_2nd)
    
    # deltax=6    
    # deltay=-7
    # T1=[42+deltax,42+deltay]
    # T2=[49+deltax,42+deltay]
    # T3=[56+deltax,42+deltay]
    # T4=[42+deltax,49+deltay]
    # T5=[49+deltax,49+deltay]
    # T6=[56+deltax,49+deltay]
    # T7=[42+deltax,56+deltay]
    # T8=[49+deltax,56+deltay]
    # T9=[56+deltax,56+deltay]  

    # deltax=0    
    # deltay=0
    # T1=[49+deltax,36+deltay]
    # T2=[55+deltax,36+deltay]
    # T3=[62+deltax,36+deltay]
    # T4=[49+deltax,42+deltay]
    # T5=[55+deltax,42+deltay]
    # T6=[62+deltax,42+deltay]
    # T7=[49+deltax,49+deltay]
    # T8=[55+deltax,49+deltay]
    # T9=[62+deltax,49+deltay]  
    
    back=patches.Rectangle([MOTray,round(MOTray/4)],waist*2, waist*2, linewidth=1, edgecolor='b', facecolor='none')
    TweezArea1=patches.Circle(T1, Tray, linewidth=1, edgecolor='r', facecolor='none')
    TweezArea2=patches.Circle(T2, Tray, linewidth=1, edgecolor='r', facecolor='none')
    TweezArea3=patches.Circle(T3, Tray, linewidth=1, edgecolor='r', facecolor='none')
    TweezerSpot1=MotSpot[T1[1]-Tray+1:T1[1]+Tray, T1[0]-Tray+1:T1[0]+Tray]
    TweezerSpot2=MotSpot[T2[1]-Tray+1:T2[1]+Tray, T2[0]-Tray+1:T2[0]+Tray]
    TweezerSpot3=MotSpot[T3[1]-Tray+1:T3[1]+Tray, T3[0]-Tray+1:T3[0]+Tray]
    TweezerSpot4=MotSpot[T4[1]-Tray+1:T4[1]+Tray, T4[0]-Tray+1:T4[0]+Tray]
    TweezerSpot5=MotSpot[T5[1]-Tray+1:T5[1]+Tray, T5[0]-Tray+1:T5[0]+Tray]
    TweezerSpot6=MotSpot[T6[1]-Tray+1:T6[1]+Tray, T6[0]-Tray+1:T6[0]+Tray]
    TweezerSpot7=MotSpot[T7[1]-Tray+1:T7[1]+Tray, T7[0]-Tray+1:T7[0]+Tray]
    TweezerSpot8=MotSpot[T8[1]-Tray+1:T8[1]+Tray, T8[0]-Tray+1:T8[0]+Tray]
    TweezerSpot9=MotSpot[T9[1]-Tray+1:T9[1]+Tray, T9[0]-Tray+1:T9[0]+Tray]
    


    if not data_frame['tweezers']:
        MotPlot(MotSpot,0,50, GaussFit=True)
    elif data_frame['tweezers']:
        if False:
            MotPlot(MotSpot,0,50)
        # Tweezer Spot n 1
        TweezerAnalysis(TweezerSpot1, 1, plotting=False, GaussFit=False)
        # Tweezer Spot n 2
        TweezerAnalysis(TweezerSpot2, 2, plotting=False, GaussFit=False)
        # Tweezer Spot n 3
        TweezerAnalysis(TweezerSpot3, 3, plotting=False, GaussFit=False) 
        # Tweezer Spot n 4
        TweezerAnalysis(TweezerSpot4, 4, plotting=False, GaussFit=False)
        # Tweezer Spot n 5
        TweezerAnalysis(TweezerSpot5, 5, plotting=False, GaussFit=False)  
        # Tweezer Spot n 6
        TweezerAnalysis(TweezerSpot6, 6, plotting=False, GaussFit=False)
        # Tweezer Spot n 7
        TweezerAnalysis(TweezerSpot7, 7, plotting=False, GaussFit=False) 
        # Tweezer Spot n 8
        TweezerAnalysis(TweezerSpot8, 8, plotting=False, GaussFit=False)
        # Tweezer Spot n 9
        TweezerAnalysis(TweezerSpot9, 9, plotting=False, GaussFit=False) 
        #Background
        # TweezerAnalysis(BGspot, 10, plotting=False, GaussFit=False)

        shot.save_result('photo_background', background_value_tosave)
        

        #2nd shot analysis
    if second_shot:
        
        TweezerSpot1_2nd=MotSpot2nd[T1[1]-Tray+1:T1[1]+Tray, T1[0]-Tray+1:T1[0]+Tray]
        TweezerSpot2_2nd=MotSpot2nd[T2[1]-Tray+1:T2[1]+Tray, T2[0]-Tray+1:T2[0]+Tray]
        TweezerSpot3_2nd=MotSpot2nd[T3[1]-Tray+1:T3[1]+Tray, T3[0]-Tray+1:T3[0]+Tray]
        TweezerSpot4_2nd=MotSpot2nd[T4[1]-Tray+1:T4[1]+Tray, T4[0]-Tray+1:T4[0]+Tray]
        TweezerSpot5_2nd=MotSpot2nd[T5[1]-Tray+1:T5[1]+Tray, T5[0]-Tray+1:T5[0]+Tray]
        TweezerSpot6_2nd=MotSpot2nd[T6[1]-Tray+1:T6[1]+Tray, T6[0]-Tray+1:T6[0]+Tray]
        TweezerSpot7_2nd=MotSpot2nd[T7[1]-Tray+1:T7[1]+Tray, T7[0]-Tray+1:T7[0]+Tray]
        TweezerSpot8_2nd=MotSpot2nd[T8[1]-Tray+1:T8[1]+Tray, T8[0]-Tray+1:T8[0]+Tray]
        TweezerSpot9_2nd=MotSpot2nd[T9[1]-Tray+1:T9[1]+Tray, T9[0]-Tray+1:T9[0]+Tray]


        if not data_frame['tweezers']:
            MotPlot(MotSpot,0,50, GaussFit=True)
        elif data_frame['tweezers']:
            if False:
                MotPlot(MotSpot,0,50)
            # Tweezer Spot n 1
            TweezerAnalysis(TweezerSpot1_2nd, 11, plotting=False, GaussFit=False)
            # Tweezer Spot n 2
            TweezerAnalysis(TweezerSpot2_2nd, 12, plotting=False, GaussFit=False)
            # Tweezer Spot n 3
            TweezerAnalysis(TweezerSpot3_2nd, 13, plotting=False, GaussFit=False) 
            # Tweezer Spot n 4
            TweezerAnalysis(TweezerSpot4_2nd, 14, plotting=False, GaussFit=False)
            # Tweezer Spot n 5
            TweezerAnalysis(TweezerSpot5_2nd, 15, plotting=False, GaussFit=False)  
            # Tweezer Spot n 6
            TweezerAnalysis(TweezerSpot6_2nd, 16, plotting=False, GaussFit=False)
            # Tweezer Spot n 7
            TweezerAnalysis(TweezerSpot7_2nd, 17, plotting=False, GaussFit=False) 
            # Tweezer Spot n 8
            TweezerAnalysis(TweezerSpot8_2nd, 18, plotting=False, GaussFit=False)
            # Tweezer Spot n 9
            TweezerAnalysis(TweezerSpot9_2nd, 19, plotting=False, GaussFit=False)  
            #Background
            # TweezerAnalysis(BGspot_2nd, 20, plotting=False, GaussFit=False)
            shot.save_result('photo_background_2nd', background_value_2nd_tosave)

    
    


#Plot the tweezers in the same picture
# plt.figure()
fig, ((ax1,ax2,ax3),(ax4,ax5,ax6),(ax7,ax8,ax9))=plt.subplots(3,3, figsize=(16,16))
fig.suptitle("Tweezer ROI - First Shot", fontsize=26)

ax1.imshow(MotSpot[T1[1]-Tray+1:T1[1]+Tray, T1[0]-Tray+1:T1[0]+Tray],cmap='plasma',vmin=0, vmax=50) #vmax=np.amax(MotSpot)
ax1.axes.get_xaxis().set_ticks([])
ax1.axes.get_yaxis().set_ticks([])
ax1.set_title('ROI 1')
ax2.imshow(MotSpot[T2[1]-Tray+1:T2[1]+Tray, T2[0]-Tray+1:T2[0]+Tray],cmap='plasma',vmin=0, vmax=50) #vmax=np.amax(MotSpot)
ax2.axes.get_xaxis().set_ticks([])
ax2.axes.get_yaxis().set_ticks([])
ax2.set_title('ROI 2')
ax3.imshow(MotSpot[T3[1]-Tray+1:T3[1]+Tray, T3[0]-Tray+1:T3[0]+Tray], cmap='plasma',vmin=0, vmax=50) #vmax=np.amax(MotSpot)
ax3.axes.get_xaxis().set_ticks([])
ax3.axes.get_yaxis().set_ticks([])
ax3.set_title('ROI 3')
ax4.imshow(MotSpot[T4[1]-Tray+1:T4[1]+Tray, T4[0]-Tray+1:T4[0]+Tray], cmap='plasma',vmin=0, vmax=50) #vmax=np.amax(MotSpot)
ax4.axes.get_xaxis().set_ticks([])
ax4.axes.get_yaxis().set_ticks([])
ax4.set_title('ROI 4')
ax5.imshow(MotSpot[T5[1]-Tray+1:T5[1]+Tray, T5[0]-Tray+1:T5[0]+Tray], cmap='plasma',vmin=0, vmax=50) #vmax=np.amax(MotSpot)
ax5.axes.get_xaxis().set_ticks([])
ax5.axes.get_yaxis().set_ticks([])
ax5.set_title('ROI 5')
ax6.imshow(MotSpot[T6[1]-Tray+1:T6[1]+Tray, T6[0]-Tray+1:T6[0]+Tray],cmap='plasma',vmin=0, vmax=50) #vmax=np.amax(MotSpot)
ax6.axes.get_xaxis().set_ticks([])
ax6.axes.get_yaxis().set_ticks([])
ax6.set_title('ROI 6')
ax7.imshow(MotSpot[T7[1]-Tray+1:T7[1]+Tray, T7[0]-Tray+1:T7[0]+Tray], cmap='plasma',vmin=0, vmax=50) #vmax=np.amax(MotSpot)
ax7.axes.get_xaxis().set_ticks([])
ax7.axes.get_yaxis().set_ticks([])
ax7.set_title('ROI 7')
ax8.imshow(MotSpot[T8[1]-Tray+1:T8[1]+Tray, T8[0]-Tray+1:T8[0]+Tray], cmap='plasma',vmin=0, vmax=50) #vmax=np.amax(MotSpot)
ax8.axes.get_xaxis().set_ticks([])
ax8.axes.get_yaxis().set_ticks([])
ax8.set_title('ROI 8')
ax9.imshow(MotSpot[T9[1]-Tray+1:T9[1]+Tray, T9[0]-Tray+1:T9[0]+Tray], cmap='plasma',vmin=0, vmax=50) #vmax=np.amax(MotSpot)
ax9.axes.get_xaxis().set_ticks([])
ax9.axes.get_yaxis().set_ticks([])
ax9.set_title('ROI 9')




TweezArea11=patches.Rectangle([T1[0]-Tray/2,T1[1]-Tray/2], Tray,Tray, linewidth=1, edgecolor='r', facecolor='none')
TweezArea21=patches.Rectangle([T2[0]-Tray/2,T2[1]-Tray/2], Tray,Tray, linewidth=1, edgecolor='r', facecolor='none')
TweezArea31=patches.Rectangle([T3[0]-Tray/2,T3[1]-Tray/2], Tray,Tray, linewidth=1, edgecolor='r', facecolor='none')
TweezArea41=patches.Rectangle([T4[0]-Tray/2,T4[1]-Tray/2], Tray,Tray, linewidth=1, edgecolor='r', facecolor='none')
TweezArea51=patches.Rectangle([T5[0]-Tray/2,T5[1]-Tray/2], Tray,Tray, linewidth=1, edgecolor='r', facecolor='none')
TweezArea61=patches.Rectangle([T6[0]-Tray/2,T6[1]-Tray/2], Tray,Tray, linewidth=1, edgecolor='r', facecolor='none')
TweezArea71=patches.Rectangle([T7[0]-Tray/2,T7[1]-Tray/2], Tray,Tray, linewidth=1, edgecolor='r', facecolor='none')
TweezArea81=patches.Rectangle([T8[0]-Tray/2,T8[1]-Tray/2], Tray,Tray, linewidth=1, edgecolor='r', facecolor='none')
TweezArea91=patches.Rectangle([T9[0]-Tray/2,T9[1]-Tray/2], Tray,Tray, linewidth=1, edgecolor='r', facecolor='none')

plt.figure() #first shot 
plt.imshow(MotSpot, cmap='plasma',vmin=0, vmax=550) #vmax=np.amax(MotSpot)
plt.rcParams.update({'font.size': 20})
plt.title('Mot Spot(first shot)')
n_ticks=5
x_values=np.round(linspace(0,(MotSpot.shape[0])*effective_pixel_size*1e6*(n_ticks-1)/n_ticks, n_ticks),1)
x_ticks=np.arange(0, MotSpot.shape[0], MotSpot.shape[0]/n_ticks)
y_values=np.round(linspace(0,(MotSpot.shape[0])*effective_pixel_size*1e6*(n_ticks-1)/n_ticks, n_ticks),1)
y_ticks=np.arange(0, MotSpot.shape[1], MotSpot.shape[0]/n_ticks)
plt.xticks(ticks=x_ticks, labels=x_values,fontsize=30)
plt.yticks(ticks=y_ticks, labels=y_values,fontsize=30)
plt.xlabel('y-axis (um)',fontsize=46)
plt.ylabel('z-axis (um)',fontsize=46)
# plt.colorbar()
cbar = plt.colorbar()
cbar.ax.tick_params(labelsize=30)
plt.gca().add_patch(TweezArea91)
plt.gca().add_patch(TweezArea81)
plt.gca().add_patch(TweezArea71)
plt.gca().add_patch(TweezArea61)
plt.gca().add_patch(TweezArea51)
plt.gca().add_patch(TweezArea41)
plt.gca().add_patch(TweezArea31)
plt.gca().add_patch(TweezArea21)
plt.gca().add_patch(TweezArea11)
saving_script(path)



#2nd image plot
if second_shot:
    plt.figure()
    plt.imshow(MotSpot2nd, cmap='plasma',vmin=0, vmax=50) #vmax=np.amax(MotSpot)
    plt.rcParams.update({'font.size': 20})
    plt.title('Mot Spot (second shot)')
    n_ticks=7
    x_values=np.round(linspace(0,(MotSpot.shape[0])*effective_pixel_size*1e6*(n_ticks-1)/n_ticks, n_ticks),2)
    x_ticks=np.arange(0, MotSpot.shape[0], MotSpot.shape[0]/n_ticks)
    y_values=np.round(linspace(0,(MotSpot.shape[0])*effective_pixel_size*1e6*(n_ticks-1)/n_ticks, n_ticks),2)
    y_ticks=np.arange(0, MotSpot.shape[1], MotSpot.shape[0]/n_ticks)
    plt.xticks(ticks=x_ticks, labels=x_values)
    plt.yticks(ticks=y_ticks, labels=y_values)
    plt.xlabel('y-axis (um)')
    plt.ylabel('z-axis (um)')
    plt.colorbar()
    # plt.gca().add_patch(TweezArea91)
    # plt.gca().add_patch(TweezArea81)
    # plt.gca().add_patch(TweezArea71)
    # plt.gca().add_patch(TweezArea61)
    # plt.gca().add_patch(TweezArea51)
    # plt.gca().add_patch(TweezArea41)
    # plt.gca().add_patch(TweezArea31)
    # plt.gca().add_patch(TweezArea21)
    # plt.gca().add_patch(TweezArea11)


    # plt.figure(200)
    fig2, ((ax1s, ax2s, ax3s),
           (ax4s, ax5s, ax6s),
           (ax7s, ax8s, ax9s)) = plt.subplots(3, 3, figsize=(16, 16))
    fig2.suptitle("Tweezer ROI - Second Shot", fontsize=26)
    ax1s.imshow(TweezerSpot1_2nd, cmap='plasma', vmin=0, vmax=50)
    ax1s.set_title('ROI 1')
    ax2s.imshow(TweezerSpot2_2nd, cmap='plasma', vmin=0, vmax=50)
    ax2s.set_title('ROI 2')
    ax3s.imshow(TweezerSpot3_2nd, cmap='plasma', vmin=0, vmax=50)
    ax3s.set_title('ROI 3')
    ax4s.imshow(TweezerSpot4_2nd, cmap='plasma', vmin=0, vmax=50)
    ax4s.set_title('ROI 4')
    ax5s.imshow(TweezerSpot5_2nd, cmap='plasma', vmin=0, vmax=50)
    ax5s.set_title('ROI 5')
    ax6s.imshow(TweezerSpot6_2nd, cmap='plasma', vmin=0, vmax=50)
    ax6s.set_title('ROI 6')
    ax7s.imshow(TweezerSpot7_2nd, cmap='plasma', vmin=0, vmax=50)
    ax7s.set_title('ROI 7')
    ax8s.imshow(TweezerSpot8_2nd, cmap='plasma', vmin=0, vmax=50)
    ax8s.set_title('ROI 8')
    ax9s.imshow(TweezerSpot9_2nd, cmap='plasma', vmin=0, vmax=50)
    ax9s.set_title('ROI 9')

    for ax in [ax1s, ax2s, ax3s, ax4s, ax5s, ax6s, ax7s, ax8s, ax9s]:
        ax.axis('off')



