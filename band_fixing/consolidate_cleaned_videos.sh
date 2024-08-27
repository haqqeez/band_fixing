#!/bin/bash

set -e # DO NOT COMMENT OUT; this ensures script aborts if any line fails
minimum_size=1M # checks to make sure cleaned videos are a reasonable size

current_directory=$(pwd)

data=$(find $pwd -type d -wholename "*/Miniscope_2/cleaned")

for session in $data
do
  cd $session
  numVideos=$(find -maxdepth 1 -type f -name "*[0-999].avi" | wc -l)
  cleaned_videos=$(find -maxdepth 1 -type f -name "*[0-999].avi")
  video_sizes_check=$(find -maxdepth 1 -type f -size +$minimum_size -name "*[0-999].avi" | wc -l)

  if (( $numVideos != $video_sizes_check )); then
    echo "ERROR: Some video files may be too small or corrupt in $session"
    exit 1
  fi

  cd ../
  mkdir -p original # mkdir if not already exists

  #shouldnt need to replace timestamp file for every bad video file, but whatever?

  cp -i "timeStamps.csv" original/
  #cp -i ./cleaned/"timeStamps.csv" .

  for video in $cleaned_videos; do
    video_number=$(basename $video)
    echo ${video_number::-4}

    read -p "WARNING: REPLACING timestamps and video $video_number in $(realpath .). Make sure you have a backup. Continue? (Y/N)" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      [[ "$0" = "$BASH_SOURCE" ]] && exit 1 || return 1 # handle exits from shell or function but don't exit interactive shell
    fi
    echo 'copying...please wait'
    cp -i $(basename $video) original/"${video_number::-4}_original.avi"
    cp -i ./cleaned/$(basename $video) .
    echo 'Done'
  done
  cd $current_directory
done
