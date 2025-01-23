import numpy as np
import cv2
import os
from glob import glob
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import json

#################################


troubleshooting = False			    # set to an integer to test only that number of consecutive videos
save = True		                    # save files
plot = False            		    # plot things

codec = 'GREY'
threshold = 0.96				    # set threshold value for detecting where bad frames occur

preserve_beginning = 6			    # number of frames to preserve at the beginning of video 0.avi (e.g., for initial TTL pulse) set to zero to ignore

ID='MYID' 					    # name date time of recording
bad_frames_dir = '/lustre04/scratch/haqqeez/badV4_frames/' # where to save bad frame png and pickle
main_videos_directory = ''			    # Miniscope directory to run analysis. Blank defaults to os.chdir()


#################################


if __name__ == "__main__":

    if not main_videos_directory:
        main_videos_directory = os.getcwd()
    os.chdir(main_videos_directory)

    if not troubleshooting:
        miniscope_videos = []
        for i in glob('*.avi'):
            try:
                miniscope_videos.append(int(i[:-4]))
            except:
                print(f'skipped {i} as it is not an integer video')
    else:
        miniscope_videos=list(np.arange(0,troubleshooting))

    # Define how many frames to include from template image
    n_frames_temp = 30
    # Read template images from concatenated video into matrix
    cap = cv2.VideoCapture('0.avi')
    # The variable video_mat will be the raw data we are going to work with below
    temp_mat = np.zeros([n_frames_temp, 
                            int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                            int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))])
    print('Filling matrix with video frames')
    for i in np.arange(n_frames_temp):
        temp_mat[i, :, :] = cap.read()[1].sum(-1) # sum across colour channels
        temp_mat[i, :, :] -= np.amin(temp_mat[i, :, :]) # normalize from max value    
        temp_mat[i, :, :] /= np.amax(temp_mat[i, :, :]) # normalize from max value

    temp_img = temp_mat.mean(0)
    # plot the template image that will be used for anomoly detection
    # This image should be completely absent of bands
    fig1 = plt.figure(figsize=(8, 8))
    ax = plt.subplot()
    ax.imshow(temp_img, cmap="gray")
    ax.set_title("Original image template", weight="bold", color="gray", fontsize=20, pad=15)
    ax.set_yticks([])
    ax.set_xticks([])
    plt.setp(ax.spines.values(), color='k', linewidth=2)
    if plot:
        plt.show()

    # determine total number of frames
    cap = cv2.VideoCapture(f'{max(miniscope_videos)}.avi')
    n_frames_tail = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    n_frames_total = n_frames_tail + 1000*(len(miniscope_videos)-1)
    print(f'Total frames is {n_frames_total}')

    bad_frame_idx = []
    good_frame_idx = []
    previous_videos_n_frames = 0
    
    
    if save:
      # save all of the bad frames
      save_dir = f'{bad_frames_dir}/{ID}_/'
  
      if not os.path.exists(save_dir):
          os.makedirs(save_dir)
    

    img_similarity = np.zeros(int(n_frames_total))

    if troubleshooting:
        num_videos = troubleshooting
    else:
        num_videos = len(miniscope_videos)

    for video in range(num_videos):
        cap = cv2.VideoCapture(f'{video}.avi')
        n_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        if video != max(miniscope_videos):
            assert n_frames == 1000, f'Video {video} has {n_frames} instead of 1000!!'

        print(f'Computing frame-wise correlations betweeen {video}.avi and template image')
        for i in np.arange(0,int(n_frames)): 
            img = cap.read()[1].sum(-1) # sum across colour channels
            img_similarity[int(i+previous_videos_n_frames)] = np.corrcoef(img.ravel(), temp_img.ravel())[0, 1]

            if video == 0 and i < preserve_beginning:
                print(f'Preserving frame #{int(i+previous_videos_n_frames)} r={(img_similarity[int(i+previous_videos_n_frames)]).round(2)}')
                good_frame_idx.append(int(i+previous_videos_n_frames))
                continue

            if img_similarity[int(i+previous_videos_n_frames)] < threshold:
                bad_frame_idx.append(int(i+previous_videos_n_frames))
                print(f'Potential bad frame #{int(i+previous_videos_n_frames)} r={(img_similarity[int(i+previous_videos_n_frames)]).round(2)}')
                
                fig = plt.figure(figsize=(8, 8))
                ax = plt.subplot()
                ax.imshow(img, cmap="viridis")
                ax.set_title(f"bad frame {int(i+previous_videos_n_frames)}", weight="bold", color="gray", fontsize=20, pad=15)
                ax.set_yticks([])
                ax.set_xticks([])
                plt.setp(ax.spines.values(), color='k', linewidth=2)
                if save:
                    fig.savefig(os.path.join(save_dir, f"{int(i+previous_videos_n_frames)}.png"), format='png')
                if plot:
                    plt.show()
                plt.clf()
                plt.close(fig)
                
            else:
                good_frame_idx.append(int(i+previous_videos_n_frames))
        previous_videos_n_frames += n_frames

    print(f'Length is {img_similarity.shape[0]}')


    # Plot the result
    sns.set(style="dark", font_scale=1.5)
    fig2 = plt.figure(figsize=(15, 5))
    ax = plt.subplot()
    ax.scatter(good_frame_idx, img_similarity[good_frame_idx], c='b', s=10)
    ax.scatter(bad_frame_idx, img_similarity[bad_frame_idx], c='Red', s=10)
    ax.axhline(threshold, c='k', linestyle='--', linewidth=2, alpha=.5)
    ax.set_xlabel('Time (30 Hz frames)')
    ax.set_ylabel('Template frame correlation \n(current frame vs template)')
    ax.set_ylim([0.5, 1.05])
    plt.legend(['good frames',
                'bad frames',
                'threshold'], loc='lower right', bbox_to_anchor=(1, 0))    
    plt.setp(ax.spines.values(), color='k', linewidth=4)
    # need to adjust n frames to be global
    plt.suptitle(f"Frame-wise anomalies ({100*len(bad_frame_idx)/n_frames_total} %)",
                    weight="bold")
    if plot:
        plt.show()
    
    # if copy of cleaned miniscope folder does not already exist, then create one
    clean_dir = main_videos_directory+ '/' + 'cleaned/'
    if glob(clean_dir) == []:
        os.mkdir(clean_dir)
    os.chdir(clean_dir)

    # read in original timeStamps.csv file as dataframe
    df = pd.read_csv(os.path.join(main_videos_directory, "timeStamps.csv"))

    # determine which video(s) are bad
    bad_video_numbers = set(np.asarray(bad_frame_idx).astype(int)//1000)

    for bad_video_number in bad_video_numbers:
        print(f"Generating cleaned miniscope video {bad_video_number}.avi")
        # read original video
        cap = cv2.VideoCapture(os.path.join(main_videos_directory, f"{bad_video_number}.avi"))
        fourcc = cv2.VideoWriter_fourcc(*codec) # Default for GREY codec    
        # create video write to save good frames to
        out = cv2.VideoWriter(os.path.join(clean_dir,f'{bad_video_number}.avi'), fourcc,
                                cap.get(cv2.CAP_PROP_FPS),
                                (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                                int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))
        t = (bad_video_number)*1000

        for i in np.arange(cap.get(cv2.CAP_PROP_FRAME_COUNT)):
            ret, frame = cap.read()
            # if the frame is in bad idx, drop it. Else write into video.
            if ret and any([t==k for k in bad_frame_idx]):  
                # drop bad idx from timeStamps
                print (f'dropping frame {t} from {bad_video_number}.avi and timeStamps.csv')
                df.drop(axis=0, index=t, inplace=True)
            else:
                out.write(frame)
            t += 1
        cap.release()
        out.release()
    df.to_csv(os.path.join(clean_dir, "timeStamps.csv"), sep=",", index=False)

    if save:
        fig1.savefig(os.path.join(clean_dir, "template.png"), format='png')
        fig2.savefig(os.path.join(clean_dir, "anomalies.png"), format='png')

        fig1.savefig(os.path.join(save_dir, "template.png"), format='png')
        fig2.savefig(os.path.join(save_dir, "anomalies.png"), format='png')

        print(f'Saving bad frames file in {save_dir}')
        os.chdir(save_dir)
        with open("all_bad_frames.json", 'w') as f:
            json.dump(bad_frame_idx, f, indent=2)
        os.chdir(main_videos_directory) # just go somewhere else so you can rename save_dir with number of bad frames
        os.rename(save_dir,f'{save_dir[:-1]}{len(bad_frame_idx)}/')
