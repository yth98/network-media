@ECHO off

IF NOT EXIST .\shape_predictor_68_face_landmarks.dat (
	IF NOT EXIST .\shape_predictor_68_face_landmarks.dat.bz2 (
		powershell -Command "Invoke-WebRequest http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2 -OutFile shape_predictor_68_face_landmarks.dat.bz2"
	)

	IF EXIST "%ProgramFiles%\WinRAR\winrar.exe" (
		"%ProgramFiles%\WinRAR\winrar.exe" x .\shape_predictor_68_face_landmarks.dat.bz2 * .\
	) ELSE ECHO "No WinRAR installation, you need to unzip shape_predictor_68_face_landmarks.dat.bz2 manually."
)

IF EXIST .\shape_predictor_68_face_landmarks.dat erase shape_predictor_68_face_landmarks.dat.bz2