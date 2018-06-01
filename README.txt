架設執行環境：
1. 執行 install/python-3.6.4-amd64.exe - Install Now!
2. 執行 b_install_opencv_and_Pillow.bat
3. 第一次執行socket時，允許通過 Windows Defender 防火牆

程式碼：
s_client_UDP.py
s_server_UDP.py
(捨棄 s_client_RTSP_over_TCP.py)

可以先不用：
1. 執行 b_install_dlib.bat
2. 執行 b_download_face-landmarks_90MB.bat (會下載90MiB的檔案!)
3. 玩玩看 s_facedet.py