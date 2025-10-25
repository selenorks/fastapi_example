# Run application
build docker image by command:

`docker build -t testapp .`

to run application

`docker run -p 8000:8000 testapp`

then you can check server on `http://127.0.0.1:8000/docs`