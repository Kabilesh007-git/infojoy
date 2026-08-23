import requests
from bs4 import BeautifulSoup


#url="https://moviesdatamil.co/idhayam-murali-2026-tamil-movie/"
#data=requests.get(url)

#print(data.content)


class request_generator :

    def __init__(self,movie_name,movie_quality):
        self.movie_name=movie_name
        self.quality=movie_quality

    def details(self):

        if self.movie_name:
            self.movie_name=str(self.movie_name).replace(" ","-")

        url=f"https://moviesdatamil.co/{self.movie_name}-2026-tamil-movie/"
        data=requests.get(url)
#----------------------------------------------------------
        with open ("details.html","wb")as dt:
            dt.write(data.content)

        with open ("details.html","rb")as dt:
            data1=dt.read()
            soup=BeautifulSoup(data1,"html.parser")
            down=soup.find("div",class_="f")
            self.link = down.find("a",href=True)["href"]
            #print(self.link)
#---------------------------------------------------------
        soup=BeautifulSoup(data.text,"html.parser")
        a=soup.find("ul")
        self.details={}
        for d in a.text.lower().splitlines():
            if d:
                key ,value=d.split(":",1)
                self.details[key.strip()]=value.strip()
        #print(self.details)    
#---------------------------------------------------------------

    def extract_id(self):
        # https://moviesdatamil.co/download/idhayam-murali-2026-original-1080p-hd/
        url=f"https://moviesdatamil.co{self.link}"

        data= requests.get(url)
        
        print(url)
        with open ("details.html","wb")as dt:
            dt.write(data.content)

        with open ("details.html","rb")as dt:
            data=dt.read()

            soup=BeautifulSoup(data,"html.parser")
            links = soup.find_all("div", class_="f")
            links = soup.find_all("div", class_="f")

            for div in links:
                a = div.find("a", href=True)

                if str(self.quality) in a["href"] :
                    self.link2=a["href"]
                    #print(self.link2)
            
            print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++step __02 __end ++++++++++++++++++++++++++++++++++++++++++++")
            


    def server_choosing(self,extract_id):
        url=f"https://moviesdatamil.co{self.link2}"
        data=requests.get(url)
        print(data.url)
        with open("details.html","wb")as dt:
            dt.write(data.content)
        soup = BeautifulSoup(data.content, "html.parser")

        dd_link=soup.select_one("div.left a[href]")
        print(dd_link["href"])
        self.link3=dd_link["href"]
        print("++++++++++++++++++++++++++++++++++++++++++++++++++ step__03__end ++++++++++++++++++++++++++++++++++++++++++++++++")

    
    def find_id(self):
        url=f"https://moviesdatamil.co{self.link3}"
        data=requests.get(url)
        print(data.url)
        with open("details.html","wb")as dt:
            dt.write(data.content)

        soup=BeautifulSoup(data.content , "html.parser")
        dlink=soup.select_one("div.download a[href]")
        self.d_link1=dlink["href"].replace("/download.moviespage.xyz/","/movies.downloadpage.xyz/").replace("/file/","/page/")
#======> https://movies.downloadpage.xyz/download/page/100756
#======> https://download.moviespage.xyz/download/page/100756


    def finel_link(self):
        url=self.d_link1
        print(self.d_link1)

        data=requests.get(url)
        with open("details.html","wb")as dt:
            dt.write(data.content)

        soup=BeautifulSoup(data.content ,"html.parser")
        d_link2=soup.select_one("div.dlink a[href]")
        print(d_link2["href"])

rg=request_generator("idhayam murali",1080)




rg.details()

rg.server_choosing()
rg.find_id()
rg.finel_link()