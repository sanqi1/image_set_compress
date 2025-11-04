import os
import numpy as np
import h5py
from PIL import Image
from PIL import UnidentifiedImageError

class Config:
    INPUT_DIR = 'data'
    OUTPUT_DIR = 'data2'
    HDF5_FILE = 'compressed_binary_images.hdf5'
    SUPPORTED_FORMATS = ('.png', '.jpg', '.jpeg', '.gif')
    MAX_FILENAME_LEN = 255  # 最大文件名长度


def scan_and_read_images():
    all_files = [
        f for f in os.listdir(Config.INPUT_DIR)
        if os.path.isfile(os.path.join(Config.INPUT_DIR, f))
    ]
    if not all_files:
        raise ValueError(f"输入目录 {Config.INPUT_DIR} 中无文件")

    image_filenames = []
    image_binaries = []

    for filename in all_files:
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in Config.SUPPORTED_FORMATS:
            print(f"跳过非图像文件：{filename}")
            continue

        file_path = os.path.join(Config.INPUT_DIR, filename)
        try:
            with Image.open(file_path):
                with open(file_path, 'rb') as f:
                    binary_data = f.read()
                if len(filename) > Config.MAX_FILENAME_LEN:
                    print(f"文件名过长，截断：{filename}")
                    filename = filename[:Config.MAX_FILENAME_LEN]
                image_filenames.append(filename)
                image_binaries.append(binary_data)
                print(f"已识别：{filename}({len(binary_data)/1024:.1f} KB)")
        except (UnidentifiedImageError, IOError) as e:
            print(f"跳过无效文件：{filename}({str(e)[:30]}...)")

    if not image_filenames:
        raise ValueError("未找到有效图像文件")

    # 按文件名排序
    sorted_pairs = sorted(zip(image_filenames, image_binaries), key=lambda x: x[0])
    return len(sorted_pairs), [p[0] for p in sorted_pairs], [p[1] for p in sorted_pairs]


def compress():
    try:
        num_images, filenames, binaries = scan_and_read_images()
        original_size = sum(len(b) for b in binaries) / 1024 / 1024
        print(f"\n开始压缩:共 {num_images} 张，原始总大小：{original_size:.2f} MB")

        filenames_padded = [
            filename.ljust(Config.MAX_FILENAME_LEN)[:Config.MAX_FILENAME_LEN]
            for filename in filenames
        ]
        filenames_array = np.array(filenames_padded, dtype=f'S{Config.MAX_FILENAME_LEN}')

        # 2. 创建HDF5文件
        with h5py.File(Config.HDF5_FILE, 'w') as h5f:
            h5f.create_dataset(
                'filenames',
                data=filenames_array,
                compression='gzip',
                compression_opts=9
            )

            binary_group = h5f.create_group('image_binaries')
            for idx in range(num_images):
                bin_dset = binary_group.create_dataset(
                    f'img_{idx}',
                    data=np.frombuffer(binaries[idx], dtype=np.uint8),
                    compression='gzip',
                    compression_opts=9
                )
                print(f"压缩进度：{idx+1}/{num_images}({filenames[idx]})")

        hdf5_size = os.path.getsize(Config.HDF5_FILE) / 1024 / 1024
        compression_rate = (1 - hdf5_size / original_size) * 100
        print(f"\n压缩完成! HDF5大小:{hdf5_size:.2f} MB,压缩率：{compression_rate:.1f}%")

    except Exception as e:
        print(f"\n压缩失败:{str(e)}")
        if os.path.exists(Config.HDF5_FILE):
            os.remove(Config.HDF5_FILE)


def decompress():
    try:
        if not os.path.exists(Config.HDF5_FILE):
            raise ValueError(f"HDF5文件 {Config.HDF5_FILE} 不存在")

        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
        print(f"解压到：{Config.OUTPUT_DIR}")

        with h5py.File(Config.HDF5_FILE, 'r') as h5f:
            # 1. 读取文件名（去除填充的空格，解码为字符串）
            filenames_array = h5f['filenames'][:]
            filenames = [
                fname.decode('ascii').rstrip()  # 去除右侧填充的空格
                for fname in filenames_array
            ]

            # 2. 读取二进制数据并还原文件
            binary_group = h5f['image_binaries']
            num_images = len(filenames)

            print(f"开始解压：共 {num_images} 张图像")
            for idx in range(num_images):
                filename = filenames[idx]
                binary_data = binary_group[f'img_{idx}'][:].tobytes()
                output_path = os.path.join(Config.OUTPUT_DIR, filename)
                with open(output_path, 'wb') as f:
                    f.write(binary_data)
                print(f"解压进度：{idx+1}/{num_images}({filename})")

        print(f"\n解压完成!")

    except Exception as e:
        print(f"\n解压失败:{str(e)}")


def main():
    import sys
    if len(sys.argv) != 2 or sys.argv[1] not in ('compress', 'decompress'):
        print("用法:")
        print("  压缩:python3 image_binary_compressor.py compress")
        print("  解压:python3 image_binary_compressor.py decompress")
        sys.exit(1)

    if sys.argv[1] == 'compress':
        print("=== 压缩模式 ===")
        compress()
    else:
        print("=== 解压模式 ===")
        decompress()


if __name__ == '__main__':
    main()