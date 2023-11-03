import cv2
import numpy as np
from statistics import mode,variance
from skimage.measure import find_contours
from skimage.morphology import thin
from domain.service.deskewing.deskewing import deskew,rotateBy
import skimage.measure as measure


def rowProjection(img):
    proj = np.sum(img,1)
    maxProjection = np.max(proj)
    result = np.zeros(img.shape)
    # Draw a line for each row
    for row in range(img.shape[0]):
        result[row,0:int(proj[row])]=1
    result=1-result
    return maxProjection,result

def calcStaffPos(rowHist,maxProjection,thr):
    n,m=rowHist.shape
    thres=int(maxProjection*thr)
    start=end=0
    width=[]
    peaksMid=[]
    for i in range(n-1):
        if(rowHist[i][thres]!=rowHist[i+1][thres]):
            if rowHist[i][thres]==1:
                #end of zeros
                start=i
            else:
                #end of ones
                end=i+1
                peaksMid.append(int((start+end)/2))
                width.append((end-start))
    return np.array(width),np.array(peaksMid)

#estimate staff segment position
def calcSegmentPos(rowHist,thres):
    n,m=rowHist.shape
    start=end=0
    width=[]
    peaksMid=[]
    for i in range(n-1):
        if(rowHist[i][thres]!=rowHist[i+1][thres]):
            if rowHist[i][thres]==1:
                #end of zeros
                start=i
            else:
                #end of ones
                end=i+1
                peaksMid.append(int((start+end)/2))
                width.append((end-start))
    return np.array(width),np.array(peaksMid)

def filterPeaks(peaksMids,widths):
    if(len(peaksMids)<=1):
        return widths,peaksMids
    newPeaks=[]
    newWidth=[]
    sumW=0
    for i in widths:
        sumW+=i
    avgW=sumW/len(widths)
    #if i dont have false peaks for clusters then this will result in a problem
    var = variance(widths)
    for i in range(len(peaksMids)):
        if(widths[i]>=avgW or (var<1000 and (avgW-widths[i])<20)):
            newPeaks.append(peaksMids[i])
            newWidth.append(widths[i])
    return newWidth,newPeaks

#divide image into segments
def imgStaffSegments(img,segMids,widths,staffS,originalImg,returnOringal):
    segments=[]
    segmentsOriginal=[]
    staffS=int(staffS)
    n,m=img.shape
    for i in range(len(segMids)):
        up=0
        down=n
        if(segMids[i]-int(widths[i]/2)-2*staffS > 0):
            up =segMids[i]- int(widths[i]/2) - 2*staffS
        if(segMids[i]+int(widths[i]/2)+2*staffS<n):
            down=segMids[i]+int(widths[i]/2)+2*staffS
        sliced= img[up:down,:]
        if(sliced.shape[0] != 0 and sliced.shape[1] != 0):
            segments.append(sliced)
            if(returnOringal):
                slicedOriginal= originalImg[up:down,:]
                segmentsOriginal.append(slicedOriginal)

    if(returnOringal):
        return segments,segmentsOriginal
    else:
        return segments

def maxStaffSpace(peaksMids,width):
    maxSpace=0
    for i in range(len(peaksMids)):
        if(i%5<4 and i+1<len(peaksMids)and peaksMids[i+1]-peaksMids[i]>maxSpace):
            maxSpace=peaksMids[i+1]-peaksMids[i]
            maxSpace=maxSpace-(width[i]/2+width[i+1]/2)
    return maxSpace

def segmenting(BinarizedImage,thres):
    #divide image into segments
    #estimate max staff space
    img = 1 - np.copy(BinarizedImage)

    maxProjection,result=rowProjection(img)
    staffWidth,peaksMids=calcStaffPos(result,maxProjection,0.6)
    maxSpace=maxStaffSpace(peaksMids,staffWidth)

    #estimate staff segment position

    segWidth,segMids=calcSegmentPos(result,thres)
    #filter peaks
    segWidth,segMids=filterPeaks(segMids,segWidth)

    #divide image into segments and divide image => return array of images each image has staff segment

    imgSegments = imgStaffSegments(img,segMids,segWidth,maxSpace,img,False)
    return imgSegments,maxSpace

def removeStaffRow(imgOriginal,midPoint,curWidth,index=0):
    thresPixel=curWidth+1
    for i in range(imgOriginal.shape[1]):
        pixelSum= sum(imgOriginal[int(midPoint-curWidth):int(midPoint+curWidth),i:i+1])
        if(pixelSum<=thresPixel):
            imgOriginal[midPoint-curWidth:midPoint+curWidth,i:i+1]=0
    return imgOriginal


def removeStaffLines(imgSegments,maxSpace=0):
    #remove staff from array of imgs of segments
    imgsStaffRemoved=[]
    segPeakMids=[]
    segWidths=[]
    tmpPeaksMids=[]
    tmpStaffWidth=[]
    maxSpace=int(maxSpace)
    for simg in imgSegments:
        maxProjection,result=rowProjection(simg)
        staffWidth,peaksMids=calcStaffPos(result,maxProjection,0.6)
        tmpPeaksMids=peaksMids
        tmpStaffWidth=staffWidth
        peaksMids=list(peaksMids)
        staffWidth=list(staffWidth)
        newWidth=staffWidth[0]+2
        peaksMids.insert(0,peaksMids[0]-maxSpace-int(staffWidth[0]/2)-int(newWidth/2))
        staffWidth.insert(0,newWidth)
        peaksMids.insert(0,peaksMids[0]-maxSpace-int(staffWidth[0]/2)-int(newWidth/2))
        staffWidth.insert(0,newWidth)
        newWidth=staffWidth[len(staffWidth)-1]+2
        peaksMids.append(peaksMids[len(peaksMids)-1]+maxSpace+int(staffWidth[len(staffWidth)-1]/2)+int(newWidth/2))
        staffWidth.append(newWidth)
        peaksMids=np.array(peaksMids)
        staffWidth=np.array(staffWidth)
        simg=simg.astype(np.float)
        ST=np.ones((2,1))
        simg=cv2.dilate(simg,ST)
        for i in range(len(peaksMids)):
            simg=removeStaffRow(simg,peaksMids[i],staffWidth[i],i)
        ST=np.ones((1,2))
        simg=cv2.dilate(simg,ST)
        simg=1-simg
        imgsStaffRemoved.append(simg)
        segPeakMids.append(tmpPeaksMids)
        segWidths.append(tmpStaffWidth)
    return imgsStaffRemoved,segPeakMids,segWidths
    #return array of images without staff

def checkOverlapped(c,imgContours):
    cXmin,cXmax,cYmin,cYmax = c
    for Xmin,Xmax,Ymin,Ymax in imgContours:
        if(cXmin > Xmin and cXmax < Xmax and cYmin >= Ymin and cYmax <= Ymax):
            return True
    return False
def filterContours(imgContours,twoDim=False,imgSlice=[]):
    filtered=[]
    filteredSlice=[]
    i=0
    for c in imgContours:
        XminC,XmaxC,YminC,YmaxC = c
        width = XmaxC - XminC
        height = YmaxC - YminC
        if height == 0 or width == 0:
            continue
        if(width<=5 and height>2*width):
            continue
        isRectH = width / height > 4 and height <= 5
        isRectV = height / width > 4 and width <= 5
        if(twoDim):
            if(not checkOverlapped(c,imgContours) and not isRectH and not isRectV):
                filtered.append(c)
                filteredSlice.append(imgSlice[i])
        else:
            if(not checkOverlapped(c,imgContours) and not isRectH and not isRectV):
                filtered.append(c)
        i+=1
    filtered.sort()
    filteredSlice.sort()
    #############################################
    for index in range(len(filtered)-1):
        XminC,XmaxC,YminC,YmaxC = filtered[index]
        XminN,XmaxN,YminN,YmaxN = filtered[index+1]
        #check for numbers to sort contours from top to down and swap them if conditions satisfied
        if (abs(XmaxC - XmaxN) <= 4 and abs (XminC - XminN) <= 4 and YminN <= YminC):
            temp = filtered[index]
            filtered[index] = filtered[index+1]
            filtered[index+1] = temp
    #############################################
    if(twoDim):
        return filtered,filteredSlice
    else:
        return filtered

def isNum(imgContours):
    isNUMList = np.zeros(len(imgContours))
    for index in range(len(imgContours)-1):
        XminC,XmaxC,YminC,YmaxC = imgContours[index]
        XminN,XmaxN,YminN,YmaxN = imgContours[index+1]
        width = XmaxC - XminC
        height = YmaxC - YminC
        ##### first condition xminC , xminN , xmaxC, xmaxN are nearly equal#####
        #####second condition ymaxC < yminN #########
        isnotNUM = height / width > 4
        if(abs(XmaxC - XminC) >= 4 and abs(XmaxN - XminN) >= 4 and YmaxC <= YminN and not isnotNUM):
            isNUMList[index] = 1
            isNUMList[index + 1] = 1
    return isNUMList

def getImageContours(imgsStaffRemoved):
    segContours=[]
    checkNumList = []
    contoursDim = []
    index=0
    for seg in imgsStaffRemoved:
        contours = find_contours(seg, 0.8)
        imgContours=[]
        imgSymbols=[]
        for contour in contours:
            x = contour[:,1]
            y = contour[:,0]
            [Xmin, Xmax, Ymin, Ymax] = [np.amin(x), np.amax(x), np.amin(y), np.amax(y)]
            imgSymbol=seg[int(Ymin):int(Ymax+1),int(Xmin):int(Xmax+1)]
            imgSymbol=1-imgSymbol
            labels = measure.label(imgSymbol)
            props = measure.regionprops(labels)
            imgSymbol=1-imgSymbol
            for prop in props:
                minr, minc, maxr, maxc = prop.bbox
                minr+=Ymin
                maxr+=Ymin
                minc+=Xmin
                maxc+=Xmin
                imgContours.append([minc, maxc, minr, maxr])


        imgContours = filterContours(imgContours)
        isNUMList = isNum(imgContours)

        for Xmin,Xmax,Ymin,Ymax in imgContours:
            imgSymbol=seg[int(Ymin):int(Ymax+1),int(Xmin):int(Xmax+1)]
            cv2.imwrite("contours/"+str(index)+".png",imgSymbol*255)
            imgSymbols.append(imgSymbol)
            index+=1

        segContours.append(imgSymbols)
        checkNumList.append(isNUMList)
        contoursDim.append(imgContours)
    return segContours,checkNumList,contoursDim
##########################################First Method for Scanned Images or when staff lines are horizontal
def staffRemoval(BinarizedImage):
    imgsegs,maxSpace = segmenting(BinarizedImage,20)
    imgsStaffRemoved,segPeakMids,segWidths = removeStaffLines(imgsegs,maxSpace)
    segContours,checkNumList,segContoursDim = getImageContours(imgsStaffRemoved)
    return segContours,segContoursDim,maxSpace,checkNumList,segPeakMids,segWidths

############################################Second Method for non horizontal staff lines
#################Utility function for second method
#################RLE to estimate staff height and staff space
def calcStaffHeightSpace(img):
    count=0
    staffHeight=[]
    staffSpace=[]
    n,m=img.shape
    lines=[]
    for j in range(m):
        start=end=0
        for i in range(n-1):
            if(img[i][j]!=img[i+1][j]):
                if img[i][j]==0:
                    #end of zeros
                    start=i
                    staffSpace.append(count)
                else:
                    #end of ones
                    end=i
                    lines.append([j,start,end,count])#colIndex,start in coloum Index,end in coloum index,thikness
                    staffHeight.append(count)
                count=0
            else:
                count+=1
        
                       
    staffHeight=mode(staffHeight)
    staffSpace=mode(staffSpace)
    return lines,staffSpace,staffHeight

def removeSymbol(img,lines,staffHeight,staffSpace):
    Thres=min(staffHeight+staffSpace,2*staffHeight)
    lines=np.array(lines)
    indices=np.where(lines[:,3]>Thres)
    staffImg=np.copy(img)
    for i in indices[0]:
        col,start,end,thres=lines[i]
        staffImg[start:end+1,col]=0
    return staffImg

def removeStaffInitial(img):
    imgLines,staffS,staffH=calcStaffHeightSpace(img)
    imgRemovedSymbols=removeSymbol(img,imgLines,staffH,staffS)
    neg=img-imgRemovedSymbols
    neg=neg.astype(np.float)
    ST=np.ones((2,3))
    neg=cv2.dilate(neg,ST)
    neg =1-neg
    return staffS,staffH,neg

def getLargestContour(img):
    contours = find_contours(img, 0.8)
    area=0
    h=w=0
    for contour in contours:
        x = contour[:,1]
        y = contour[:,0]
        [Xmin, Xmax, Ymin, Ymax] = [np.amin(x), np.amax(x), np.amin(y), np.amax(y)]
        curH = Ymax-Ymin
        curW = Xmax-Xmin
        if(curH*curW > area):
            area = curH*curW
            h = curH
            w = curW
    return h,w


#convert image into contours
def getContoursDeskewed(imgWithStaff,imgWithoutStaff):
    contours = find_contours(imgWithoutStaff, 0.8)
    imgContours=[]
    imgRealDim=[]
    imgSymbols=[]
    imgSymbolsNoStaff=[]
    aspects=[]
    widths=[]
    heights=[]
    yMins=[]
    index=0
    h = imgWithStaff.shape[0]
    errorRotation=[]
    for contour in contours:
        x = contour[:,1]
        y = contour[:,0]
        [Xmin, Xmax, Ymin, Ymax] = [np.amin(x), np.amax(x), np.amin(y), np.amax(y)]
        imgContours.append([Xmin, Xmax, 0, h])
        imgRealDim.append([Xmin, Xmax, Ymin, Ymax])

    imgRealDim,imgContours = filterContours(imgRealDim,True,imgContours)
    isNUMList = isNum(imgRealDim)

    for Xmin,Xmax,Ymin,Ymax in imgRealDim:
        yMins.append(Ymin)
        imgSymbol = imgWithStaff[0:h,int(Xmin):int(Xmax+1)]
        imgSymbolNoStaff = imgWithoutStaff[0:h,int(Xmin):int(Xmax+1)]

        imgSymbol = 1 -imgSymbol
        thinned = thin(imgSymbol)
        thinned,angle = deskew(thinned,True,1)
        imgSymbol = rotateBy(imgSymbol,angle)
        imgSymbol = 1 - imgSymbol

        #get vertical images

        imgSymbolNoStaff = 1 -imgSymbolNoStaff
        thinned = thin(imgSymbolNoStaff)
        thinned,angle = deskew(thinned,True,0)
        if(abs(angle) <=15):
            errorRotation.append(0)
        elif(abs(angle) <=30):
            errorRotation.append(1)
        else:
            errorRotation.append(2)
        imgSymbolNoStaff = rotateBy(imgSymbolNoStaff,angle)

        imgSymbolNoStaff = 1 -imgSymbolNoStaff

        cHeight,cWidth = getLargestContour(imgSymbolNoStaff)
        
        aspects.append(cHeight/cWidth)
        widths.append(cWidth)
        heights.append(cHeight)

        imgSymbols.append(imgSymbol)
        imgSymbolsNoStaff.append(imgSymbolNoStaff)
        index+=1
    return imgSymbols,imgSymbolsNoStaff,imgContours,isNUMList,aspects,errorRotation,widths,heights,yMins

#################Second method

def staffRemovalNonHorizontal(BinarizedImage):
    staffS,staffH,staffFree = removeStaffInitial(1-BinarizedImage)
    staffS+=1
    maxProjection,result=rowProjection(1-staffFree)
    #estimate staff segment position
    segWidth,segMids=calcSegmentPos(result,60)
    #filter peaks
    segWidth,segMids=filterPeaks(segMids,segWidth)
    #divide image into segments and divide image => return array of images each image has staff segment of staff removed and original one
    imgSegments,imgSegmentsStaff = imgStaffSegments(staffFree,segMids,segWidth,staffS,BinarizedImage,True)
    segContours=[]
    segContoursDim=[]
    checkNumList=[]
    segContoursPeakmids=[]
    segContoursWidth=[]
    segAspects=[]
    dimWidth=[]
    dimHeight=[]
    Ys=[]
    i=0
    for imgSeg in imgSegments:
        imgContours,imgContoursNoStaff,imgContoursDim,isNum,aspects,errorRotation,w,h,yMins = getContoursDeskewed(imgSegmentsStaff[i],imgSeg)
        segContourWidth=[]
        segContourPeakmids=[]
        #remove staff from array of imgs
        index=0
        for cimg in imgContours:
            cimg=1-cimg
            maxProjection,result=rowProjection(cimg)
            staffWidth,peaksMids=calcStaffPos(result,maxProjection,0.9)
            peaksMids-=errorRotation[index]
            segContourWidth.append(staffWidth)
            segContourPeakmids.append(peaksMids)
            index+=1
        segContoursDim.append(imgContoursDim)
        segContours.append(imgContoursNoStaff)
        checkNumList.append(isNum)
        segContoursPeakmids.append(segContourPeakmids)
        segContoursWidth.append(segContourWidth)
        segAspects.append(aspects)
        dimWidth.append(w)
        dimHeight.append(h)
        Ys.append(yMins)
        i+=1
    return segContours,segContoursDim,staffS,checkNumList,segContoursPeakmids,segContoursWidth,segAspects,dimWidth,dimHeight,Ys