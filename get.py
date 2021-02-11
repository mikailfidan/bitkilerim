# encoding:utf-8
from bs4 import BeautifulSoup
import requests, re, sqlite3, time, os, subprocess
import pandas as pd
import tkinter.scrolledtext as st 
import tkinter as tk



win=tk.Tk()
win.title('Bitkilerim')
win.geometry('550x280')

db=sqlite3.connect('bitkilerim.db')
cs=db.cursor()
count=0


def fileExist(file):
    return os.path.exists(file)

if fileExist('list.xlsx'):
    l1=tk.Label(win,text='-list.xlsx exist', fg='green')
    l1.pack()
else:
    l1=tk.Label(win,text='-list.xlsx not exist', fg='red')
    l1.pack()
    
if fileExist('bitkilerim.db'):
    l2=tk.Label(win,text='-bitkilerim.db exist', fg='green')
    l2.pack()
else:
    l2=tk.Label(win,text='-bitkilerim.db not exist', fg='red')
    l2.pack()

if fileExist('bitkilerim.db')==True and fileExist('list.xlsx')==True:
    b1=tk.Button(win,text='Start',command=lambda:callAllDef())
    b1.pack()
 
labelframe = tk.LabelFrame(win, text='Output:')
labelframe.pack(fill='both', expand='yes')
text_area = st.ScrolledText(labelframe, wrap=tk.WORD, width=400, font = ('Times New Roman',12))
text_area.config(background='black', foreground='white')
text_area.get(1.0)
text_area.pack(side='left', fill='x')
text_area.insert(tk.INSERT,'sourcecode : https://github.com/mikailfidan\n')
 

def insertText(textString, sleep=0):
    global text_area
    text_area.insert(tk.INSERT, textString)
    time.sleep(sleep)
    text_area.see(tk.END)
    win.update()
    

def setEnedemik(tur):
    cs.execute('update bitkilerim SET ENDEMIKMI="TRUE" WHERE TUR=?',(tur,))

def setYazar(yazar,tur):
    cs.execute('update bitkilerim SET YAZAR=? WHERE TUR=?',(yazar,tur,))

def setSiteID(siteid,tur):
   cs.execute('update bitkilerim SET SITE_ID=? WHERE  TUR=?',(siteid,tur,))

def setElement(siteid, element):
    cs.execute('update bitkilerim SET ELEMENT=? WHERE SITE_ID=?',(element,siteid))

def reCreateDB():
    global count
    cs.execute('DELETE FROM bitkilerim')
    insertText('#Droped Table\n',1)
    bitkilerimExcel=pd.read_excel('list.xlsx',sheet_name='Sayfa1')
    insertText('-Getting data from excel file...\n',1)
    bitkilerimExcel.to_sql(name='bitkilerim', con=db, if_exists='replace', index=False)
    count=len(cs.execute('select * from bitkilerim').fetchall())
    db.commit()
    
    
    

def getData():
    global count
    insertText('#Getting data from web site...\n',2)
    data=cs.execute('SELECT TUR from bitkilerim WHERE ALTTUR IS NULL AND VARYETE IS NULL').fetchall()
    dataCount=str(len(data))
    insertText('{} items found\n'.format(dataCount),1)
      
    for row in data:
        r=requests.get('https://bizimbitkiler.org.tr/yeni/demos/technical/accepted.php?q='+row[0]+'&type=TBL')
        source=BeautifulSoup(r.content,'html.parser')
        tdAll=source.find_all('td')
        
        if len(tdAll)>0:
            button=str(source.find_all('button'))
            getid=re.search('(?<=showDetails\(\').\d+', button)
            tdvalues=''
        
            for td in tdAll:
                tdvalue=td.text.strip()
                if tdvalue not in ('Göster','GÃ¶ster'):
                    tdvalues=tdvalues+tdvalue+' '
            
            if getid is not None:
                setSiteID(getid.group(0),row[0])        

            if 'ENDEMİK' in tdvalues:
                setEnedemik(row[0])
            
            setYazar(tdvalues, row[0])
            insertText('['+str(count)+'] Saved : '+ tdvalues+'\n')
            if getid is not None:
                setSiteID(getid.group(0), row[0])
            db.commit()
        else:
            insertText('['+ str(count)+']' +row[0]+ ' not found\n',1)
            
        count-=1 if count>0 else count
               
   
def getDataVar(arg):
    global count
    query='SELECT TUR, VARYETE from bitkilerim WHERE VARYETE NOT NULL'
    if arg!='var':
        query='SELECT TUR, ALTTUR from bitkilerim WHERE ALTTUR NOT NULL'

    insertText('#' + str(arg).upper()+ ' has been selected\n')
    time.sleep(2)
    dataVar=cs.execute(query).fetchall()
    dataVarCount=str(len(dataVar))
    insertText('{} items found\n'.format(dataVarCount),1)
    

    for row in dataVar:
        r=requests.get('https://bizimbitkiler.org.tr/yeni/demos/technical/accepted.php?q='+row[0]+'&type=TBL')
        source=BeautifulSoup(r.content,'html.parser')
        tdAll=source.find_all('td')
    
        if len(tdAll)>0:
            endsWithShowDetail=re.search('(?<='+re.escape(arg)+'\.\s'+re.escape(row[1])+'.).\w+[^G]+', str(tdAll))
            if endsWithShowDetail is not None:
                getid=re.search('(?<=showDetails\(\').\d+', endsWithShowDetail.group(0))
                getAuthor=re.search('(?<='+re.escape(arg)+'\.\s'+re.escape(row[1])+'.).\w+[^<]+', str(tdAll))

                if 'ENDEMİK' in endsWithShowDetail.group(0):
                    setEnedemik(row[0])
                    
                if getAuthor is not None:
                    setYazar(getAuthor.group(0), row[0])
                    insertText('['+str(count)+'] Saved : '+ getAuthor.group(0)+'\n')

                if getid is not None:
                    setSiteID(getid.group(0), row[0])
                db.commit()    
        else:
            insertText('['+ str(count)+']' +row[0]+ ' not found\n',1)
        
        count-=1 if count>0 else count
        
def getElement():
    insertText('\n#Getting Elements...\n',2)
    dataElement=cs.execute('SELECT SITE_ID, ELEMENT, TUR FROM bitkilerim').fetchall()
    countElement=len(dataElement)
    insertText('-'+str(countElement)+' items found\n')

    for row in dataElement:
        if row[0] is not None:
            r=requests.get('https://bizimbitkiler.org.tr/yeni/demos/technical/getDetails.php?id='+str(int(row[0]))+'&type=accepted')
           
            source=BeautifulSoup(r.content,'html.parser')
            tdAll=source.find_all('span',{'class':'label-success'})
            if len(tdAll)>0:
                for td in tdAll:
                    setElement(row[0],  td.text.strip())
                    insertText('['+str(countElement)+'] Saved: element of '+ row[2]+'\n')
                    db.commit()
        else:
            insertText('['+ str(countElement)+']' +row[2]+ ' not found\n',1)
        countElement-=1

def exportXLS():
    insertText('\n#Exporting as exportData.xlsx...\n',1)
    bitkilerimDB = pd.read_sql('select * from bitkilerim', con=db)
    bitkilerimDB.to_excel('exportData.xlsx', index = False, header=True)
    

def callAllDef():
   
    insertText('Starting...\n')
    try:
        reCreateDB()
    except Exception as e:
        insertText ('\n!!! Error occured in reCreateDB()\n -'+str(e)+'\n',1)
        pass

    try:
        getData()
    except Exception as e:
        insertText ('\n!!!Error occured in getData()\n -'+str(e)+'\n',1)
        pass

    try:
        getDataVar('var')
       
    except Exception as e:
        insertText('\n!!!Error occured in getDataVar(var)\n -'+str(e)+'\n',1)
        pass

    try:
        getDataVar('subsp')
    except Exception as e:
        insertText('\n!!!Error occured in getDaVar(sub)\n -'+str(e)+'\n',1)
        pass

    try:
        getElement()
    except Exception as e:
        insertText('\n!!!Error occured in getElement(sub)\n -'+str(e)+'\n',1)
        pass

    try:
        exportXLS()
    except Exception as e:
        insertText('\n!!!Error occured in exportXLS()\n -'+str(e)+'\n',1)
        pass
    insertText('\n### Program End. ###')
    

win.mainloop()