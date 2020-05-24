from django.http import HttpResponseRedirect
from django.core.files.base import ContentFile
from .models import api
from editing import settings
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
from PIL import Image
import base64 , requests
import random
import string
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
import sys
import platform

def removebg(path):
    # foo=Image.open(path)
    # foo.save(path, quality=30)
    img = cv.imread(path, cv.IMREAD_UNCHANGED)
    original = img.copy()
    l = int(max(5, 6))
    u = int(min(6, 6))
    edges = cv.GaussianBlur(img, (21, 51), 3)
    edges = cv.cvtColor(edges, cv.COLOR_BGR2GRAY)
    edges = cv.Canny(edges, l, u)
    _, thresh = cv.threshold(edges, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5))
    mask = cv.morphologyEx(thresh, cv.MORPH_CLOSE, kernel, iterations=4)
    data = mask.tolist()
    sys.setrecursionlimit(10 ** 8)
    for i in range(len(data)):
        for j in range(len(data[i])):
            if data[i][j] != 255:
                data[i][j] = -1
            else:
                break
        for j in range(len(data[i]) - 1, -1, -1):
            if data[i][j] != 255:
                data[i][j] = -1
            else:
                break
    image = np.array(data)
    image[image != -1] = 255
    image[image == -1] = 0

    mask = np.array(image, np.uint8)

    result = cv.bitwise_and(original, original, mask=mask)
    result[mask == 0] = 255  # white background

    cv.imwrite(path, result)
    img = Image.open(path)
    img.convert("RGBA")
    datas = img.getdata()
    newData = []
    for item in datas:
        if item[0] == 255 and item[1] == 255 and item[2] == 255:  # checking white
            newData.append((255, 255, 255, 0))  # setting alpha to 0
        else:
            newData.append(item)

    img.putdata(newData)
    img.save(path, "PNG",optimize=True,quality=85)



def home(request):
    return render(request,'index.html')



def funname():
    name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=25))
    name_bytes = name.encode('ascii')
    name = base64.b64encode(name_bytes)
    name = name.decode('ascii')
    name = name.replace("=", "").lower()
    return name

def upload(request):
    if request.method=='POST':
        photo=request.FILES.getlist('file')
        txt=''
        fs = FileSystemStorage()
        ses=[]
        data=[]
        for i in photo:
            img=['jpg','jpeg','png']
            imgmane=i.name
            ext=imgmane.split('.')
            ext=ext[1].lower()
            size = i.size
            # print(size)
            if ext in img:
                ext='png'
                name= funname()
                name=name+'.'+ext
                save = fs.save(name, i)
                url = fs.url(save)
                aa=api.objects.all()
                api_key=''
                for k in aa:
                    if k.count <=49:
                        ids=k.id
                        api_key=k.api
                        count=k.count
                        break
                #print(ids)
                #print(api_key)
                #print(count)



                paths=settings.BASE_DIR+'/static'+url
                #print(paths)
                response=  requests.post(
                                'https://api.remove.bg/v1.0/removebg',
                                files={'image_file': open(paths, 'rb')},
                                data={'size': 'auto'},
                                headers={'X-Api-Key': api_key},
                            )
                if response.status_code == requests.codes.ok:
                    with open(paths , 'wb') as out:
                        out.write(response.content)



                counts = count + 1
                api.objects.filter(id=ids).update(count=counts)

                # if platform.system() == 'Windows':
                #     paths = paths.replace('/', '\\')
                # path=sys.path[0]+paths
                #
                # # print(path)
                foo=Image.open(paths)
                # # foo.resize((x,y),Image.ANTIALIAS)
                foo.save(paths,optimize=True,quality=30)
                # print(foo.size)
                # removebg(path)


                with open(paths,'rb') as f:
                    my_string = base64.b64encode(f.read()).decode('utf-8')
                    im_dat ='data:image/png;base64,'+my_string

                print(im_dat)
                data.append(im_dat)
                ses.append(url)
            else:
                txt='Upload error'



        context={'url':ses ,'image':data ,'error':txt}
        return render(request, 'index2.html',context)
    else:
        return home(request)

