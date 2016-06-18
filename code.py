#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
import boto3
import os
import sys, traceback

# ここを自分の番号にあわせてください
MY_NUMBER='00'

FRAME_FILE='materials/gamecard_frame_gold.png'
EFFECT_FILE='shuchu-sen01.png'

s3 = boto3.client('s3')

def mask_img(img1, img2):
    mask = img2[:,:,3]
    mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    mask = mask / 255
    img2 = img2[:,:,:3]
    img1 *= 1 - mask
    img1 += img2 * mask

    return img1

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    print u'Bucket=' + bucket
    print u'key=' + key

    tmpfile = u'./work/' + os.path.basename(key)
    output = u'card' + MY_NUMBER + '.jpg'

    # カードのサイズ
    card_w = 360
    card_h = 500

    try:
        s3.download_file(Bucket=bucket, Key=key, Filename=tmpfile)

        src = cv2.imread(tmpfile)
        src_w, src_h = src.shape[:2]

        # 元の画像から必要な部分だけ切り抜く
        trim_x = 50
        trim_width = card_w
        trim_y = 0
        trim_height = src_w * card_h / card_w
        img = src[trim_y:trim_y+trim_height, trim_x:trim_x+trim_width]
        img = cv2.resize(img, (card_w, card_h))

        # カードフレームを読み込んで画像に被せる
        frame = cv2.imread(FRAME_FILE, cv2.IMREAD_UNCHANGED)
        frame = cv2.resize(frame, (card_w, card_h))
        img = mask_img(img, frame)

        # テキストを書き込む
        font_size = 1
        text = "RARE!!"
        cv2.putText(img, text, (card_w/2 - len(text) * font_size * 18 / 2, card_h - 20), cv2.FONT_HERSHEY_COMPLEX, 1, (0,0,0))

        # 画像を保存する
        cv2.imwrite(output, img)
        s3.upload_file(Bucket='geeklab-joetsu', Key='card/' + output, Filename=output)

    except Exception, e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback)
        raise e

# メイン関数
if __name__ == "__main__":
    event = {
        'Records': [
            { 's3':
                {
                    'bucket': { 'name': 'geeklab-joetsu' },
                    'object': { 'key':  'src/img' + MY_NUMBER + '.jpg' }
                }
            }
        ]

    }
    lambda_handler(event, {})
