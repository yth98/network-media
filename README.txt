使用前請先架設執行環境：
1. 安裝 Python 3.6.4
2. 執行 b_install_opencv_and_Pillow.bat
3. 執行 b_install_dlib.bat
4. 執行 b_download_face-landmarks_90MB.bat (會下載90MiB的檔案!)
5. 第一次執行socket時，允許通過 Windows Defender 防火牆

主程式：
s_client_UDP.py
s_server_UDP.py

套件 mod：
face.py
	{cv2 image} face_proc(pix {as cv2 image})
tts_itri.py
	{wav binary} text2wav(saytext {as string})