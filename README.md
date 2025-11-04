# Image Set Compress

## Usage

#### HDF5+gzip压缩

- 安装依赖

```
pip install -r requirements.txt
```

- 压缩

```
python3 image_binary_compressor.py compress
```

- 解压

```
python3 image_binary_compressor.py decompress
```





#### 7z压缩

- 安装

```
sudo apt install p7zip-full
```

- 压缩

```
7z a -t7z -mx=9 images_compressed2.7z data/*
```

- 解压

```
7z x images_compressed.7z -odata2/
```

