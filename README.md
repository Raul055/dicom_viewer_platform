# DICOM Platform

This plataform is focused on the administration and management of DICOM images between patients and medics via remote. With this platform, medics can access easily DICOM images from patients in order to improve diagnostic times and accesability.

## Instalation
The installation of this platform is easily acces via git. For it, just clone the repository.
```
git clone https://github.com/Raul055/dicom_viewer_platform.git
```

## Setup
Run the following command to install all dependencies (python is needed to run `pip`).
```
pip install -r requirements.txt
```

Then, after all dependencies are installed, run `run.py`.
```
python run.py
```

The server will run locally and all devices in your network can access to it. This can be also deployed if wanted.