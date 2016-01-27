=================================
Video Pseudo Streaming with Nginx
=================================


----------
MP4 / H264
----------

Converting flv to mp4

    ffmpeg -i input_file -c:a aac -strict -2 -b:a 128k -c:v libx264 -profile:v baseline out.mp4

name=`basename ${1} .mpg`
avconv -i ${name}.mpg -vcodec libx264 -b:v 600k -maxrate 600k -bufsize 1000k -deinterlace -threads 0 -acodec libvo_aacenc -b:a 96k ${name}.mp4
avconv -i ${name}.mpg -s 4cif -ab 96k -vb 600k -deinterlace -aspect "16:9" ${name}.webm


------------
Flash Videos
------------

Install flvtool2

    sudo gem install flvtool2


Prepare flv files for streaming

    flvtool2 -U <video_file>.flv


----------------
Background links
----------------


http://snippets.aktagon.com/snippets/132-how-to-install-ffmpeg-mencoder-and-flvtool2-on-mac-osx-leopard-convert-an-avi-to-flv-and-view-the-flv-video-with-flowplayer