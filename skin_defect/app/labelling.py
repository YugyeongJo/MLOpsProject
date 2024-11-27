import os
import cv2
import matplotlib.pyplot as plt

def check(pic, label, output_dir):
    # 파일 경로 확인
    if not os.path.exists(pic):
        print(f"Error: {pic} 경로를 찾을 수 없습니다.")
        return
    if not os.path.exists(label):
        print(f"Error: {label} 경로를 찾을 수 없습니다.")
        return
    
    # 라벨 파일 열기
    with open(label, 'r') as file:
        dp = file.readlines()
    
    picture = plt.imread(pic)
    copy = picture.copy()
    height, width = copy.shape[:2]
    blue_color = (255, 0, 0)
    
    # 라벨 처리
    for i in dp:
        c, x, y, w, h = i.split(' ')
        c, x, y, w, h = float(c), float(x), float(y), float(w), float(h)
        start = ((x * width - 0.5 * w * width), (y * height - 0.5 * h * height))
        end = ((x * width + 0.5 * w * width), (y * height + 0.5 * h * height))
        start = (int(start[0]), int(start[1]))
        end = (int(end[0]), int(end[1]))
        result = cv2.rectangle(copy, start, end, blue_color, 3)
    
    # 결과 저장
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, os.path.basename(pic))
    cv2.imwrite(output_path, cv2.cvtColor(result, cv2.COLOR_RGB2BGR))
    
    plt.figure(figsize=(10, 10))
    plt.imshow(result)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def process_images(image_dir, label_dir, output_dir):
    # 디렉토리 내 이미지 파일 처리
    for image_name in os.listdir(image_dir):
        if image_name.endswith(('.jpg', '.jpeg', '.png')):
            image_path = os.path.join(image_dir, image_name)
            label_name = image_name.replace('.jpg', '.txt').replace('.jpeg', '.txt').replace('.png', '.txt')
            label_path = os.path.join(label_dir, label_name)
            check(image_path, label_path, output_dir)

# 이미지와 라벨 폴더 경로
image_folder = "/Users/dongwoohan/Desktop/SESAC_Final/ddataset/psoriasis/test/images"
label_folder = "/Users/dongwoohan/Desktop/SESAC_Final/ddataset/psoriasis/test/labels"
output_folder = "/Users/dongwoohan/Desktop/SESAC_Final/ddataset/psoriasis/test/output"

process_images(image_folder, label_folder, output_folder)
