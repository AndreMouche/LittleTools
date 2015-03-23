#!/bin/bash

# build shell base on the ffmpeg-2.2.2
# audiotrans AAC/amr/mp3/mp2/flac/ogg/ac3/wav/wma/wmv  to mp3/amr/aac
# System:
#Linux ubuntu 3.13.0-32-generic #57-Ubuntu SMP Tue Jul 15 03:51:08 UTC 2014 x86_64 x86_64 x86_64 GNU/Linux 

./configure \
    --extra-cflags='-I/usr/include -static' \
    --extra-ldflags='-I/usr/lib -static' \
    --disable-debug \
    --disable-shared \
    --enable-static \
    --enable-gpl \
    --enable-libmp3lame \
    --enable-nonfree \
    --disable-logging \
    --disable-avdevice \
    --disable-postproc \
    --disable-dxva2 \
    --disable-vaapi \
    --disable-vda \
    --disable-vdpau \
    --disable-everything \
    --disable-runtime-cpudetect \
    --disable-ffplay \
    --disable-ffprobe \
    --disable-ffserver \
    --disable-doc \
    --disable-htmlpages \
    --disable-manpages \
    --disable-podpages \
    --disable-txtpages \
    --enable-protocol=file \
    --enable-protocol=pipe \
    --enable-protocol=http \
    --enable-protocol=https \
    --enable-filter=aresample \
   --enable-decoder=mp3 \
    --enable-demuxer=mp3 \
    --enable-parser=mpegaudio \
    --enable-muxer=mp3 \
    --enable-encoder=libmp3lame \
	--enable-version3 \
    --enable-libvo-aacenc \
    --enable-libfdk_aac \
    --enable-libfdk-aac \
    --enable-libfaac \
    --enable-parser=aac \
    --enable-encoder=aac \
    --enable-decoder=aac \
    --enable-encoder=libfaac \
    --enable-encoder=libvo_aacenc \
    --enable-encoder=libaacplus \
    --enable-encoder=libfdk_aac \
    --enable-decoder=libfdk_aac\
	--enable-demuxer=aac \
    --enable-muxer=adts \
    --enable-libopencore-amrnb \
	--enable-libopencore-amrwb \
	--enable-libvo_amrwbenc \
    --enable-encoder=libvo_amrwbenc \
    --enable-decoder=libopencore_amrnb \
	--enable-encoder=libopencore_amrnb \
    --enable-decoder=libopencore_amrwb \
    --enable-decoder=amrnb \
    --enable-decoder=amrwb \
	--enable-muxer=amr \
    --enable-demuxer=amr \
    --enable-libwavpack \
    --enable-muxer=wav \
    --enable-demuxer=wav \
    --enable-decoder=wavpack \
    --enable-encoder=wavpack \
    --enable-encoder=pcm_s16le \
    --enable-decoder=pcm_s16le \
    --enable-libvorbis \
    --enable-parser=vorbis \
    --enable-encoder=vorbis \
    --enable-decoder=vorbis \
    --enable-encoder=libvorbis \
    --enable-decoder=libvorbis \
    --enable-muxer=ogg \
    --enable-demuxer=ogg \
    --enable-decoder=mp1float \
    --enable-decoder=mp1 \
    --enable-encoder=mp2 \
    --enable-decoder=mp2 \
    --enable-muxer=mp2 \
    --enable-decoder=mp2float \
    --enable-encoder=mp2fixed \
    --enable-encoder=flac \
    --enable-decoder=flac \
    --enable-demuxer=flac \
    --enable-muxer=flac \
    --enable-parser=flac \
    --enable-encoder=ac3 \
    --enable-decoder=ac3 \
    --enable-encoder=ac3_fixed\
    --enable-decoder=atrac3 \
    --enable-decoder=atrac3p \
    --enable-encoder=eac3 \
    --enable-decoder=eac3 \
    --enable-muxer=ac3 \
    --enable-demuxer=ac3 \
    --enable-muxer=eac3 \
    --enable-demuxer=eac3 \
    --enable-decoder=wmalossless \
    --enable-decoder=wmapro \
    --enable-encoder=wmav1 \
    --enable-decoder=wmav1 \
    --enable-encoder=wmav2 \
    --enable-decoder=wmav2 \
    --enable-decoder=wmavoice \
    --enable-demuxer=xwma \
    --enable-demuxer=avi \
    --enable-muxer=avi \
    --enable-demuxer=asf \
    --enable-muxer=asf \
    --enable-encoder=wmv1 \
    --enable-decoder=wmv1 \
    --enable-encoder=wmv2 \
    --enable-decoder=wmv2 \
    --enable-decoder=wmv3 \
    --enable-decoder=wmv3_crystalhd \
    --enable-decoder=wmv3_vdpau \
    --enable-decoder=wmv3image \
    --enable-encoder=jpeg2000 \
    --enable-encoder=mjpeg \
    --enable-encoder=ljpeg \
    --enable-encoder=jpegls \
    --enable-decoder=jpeg2000 \
    --enable-decoder=jpegls \
    --enable-decoder=mjpeg \
    --enable-decoder=mjpegb \
    --enable-muxer=mjpeg \
    --enable-demuxer=mjpeg \
    --enable-encoder=png \
    --enable-decoder=png \
    --enable-parser=png \
    --enable-swscale \
    --enable-swscale-alpha \
    --enable-filter=scale \
    --enable-encoder=pcm_u8 \
    --enable-decoder=pcm_u8 \
    --enable-muxer=pcm_u8 \
    --enable-demuxer=pcm_u8 \
    --enable-small \
#   --enable-encoder=mpeg* \
#    --enable-decoder=mpeg* \
#    --enable-encoder=msmpeg4* \
#    --enable-decoder=msmpeg4* \
#    --enable-muxer=mpeg* \
#    --enable-demuxer=mpeg* \
#
#
#
#make -j 2

#./ffmpeg -v 0 -formats

#ls -lh ffmpeg

