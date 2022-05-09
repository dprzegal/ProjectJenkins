import configparser
import jenkins
from datetime import datetime
import os,sys
from fileinput import filename

class JenkinsConnection():
    def __init__(self, config_file,log_filename):
        self.username = ''
        self.password = ''
        self.server = ''
        self.port = 8080
        self.config_file = config_file
        self.log_filename = log_filename


    def getConfig(self):
        config = configparser.ConfigParser()
        return config

    def getJenkinsCredentials(self):
        # read the configuration file
        self.config = self.getConfig()
        self.config.read(self.config_file)
        # get all the connections
        c = self.config.sections()
        #retrieve the connection sections like Jenkins and others
        #get credentials
        for i in c:
            if i == 'Jenkins':
                self.username = self.config.get(i,'username')
                self.password = self.config.get(i,'password')
                self.server = self.config.get(i,'server')
                self.port = self.config.get(i,'port')
       
    
    def connectToJenkins(self):
        # connect to Jenkins server
        self.serverurl = 'http://'+self.server+':'+self.port
        try:
            self.serverconn = jenkins.Jenkins(self.serverurl, self.username, self.password)
            user = self.serverconn.get_whoami()
            version = self.serverconn.get_version()
            print('Hello %s from Jenkins %s' % (user['fullName'], version))
            f = open(log_filename,"a")
            f.write("connecting to Jenkins...\n" )
            f.close
            return self.serverconn
        except ConnectionError:
            print("Jenkins connection failed")
            f = open(log_filename,"a")
            f.write("error while connecting to Jenkins, connection failed\n" )
            f.close
            exit

class JenkinsOperations():
    
    def __init__(self,Jenkins_connection_obj):
        self.Jenkins_connection_obj = Jenkins_connection_obj
        self.Jenkins_connection_obj.getJenkinsCredentials()
        self.serverconn = Jenkins_connection_obj.connectToJenkins()
    
    def JobsAmount(self):
        j = self.serverconn.jobs_count()
        return j
            
    def printJobsAmount(self):
        print("Jobs amount:",self.JobsAmount())
    
    def AllJobs(self):
        jobs = self.serverconn.get_all_jobs()
        i=0
        jobs_list = []
        for job in jobs:
            jobname = job['fullname']
            last_nr = self.lastBuildNr(jobname)
            jobs_dic = {}
            jobs_dic["job_nr"] = i+1          
            jobs_dic["job_name"] = jobname
            jobs_dic["builds"] = last_nr
            jobs_dic["last_build_date"] = self.BuildDate(jobname, last_nr)
            jobs_dic["who_started_build"] = self.BuildWho(jobname, last_nr)
            jobs_dic["success_build"] = self.buildState(jobname, last_nr)
            i+=1
            jobs_list.append(jobs_dic)
        return jobs_list
    
    def printAllJobsLastBuildInfo(self):
        jobs = self.serverconn.get_all_jobs()
        i=1
        print("Job id: |Job name:   |Build number: ")
        for job in jobs:
            jobname = job['fullname']
            print("Job",i,": ",jobname)
            i+=1
            #last build number:
            last_nr = self.lastBuildNr(jobname)
            self.printBuildNumber(last_nr)
            self.printBuildDate(jobname,last_nr)
            self.printBuildWho(jobname,last_nr)
            self.printBuildState(jobname, last_nr)
            print()
        f = open(log_filename,"a")
        f.write("fetching data from Jenkins...\n" )
        f.close
        
    def printAllJobsInfo(self):
        jobs = self.serverconn.get_all_jobs()
        i=1
        print("Job id: |Job name:   |Build number: ")
        for job in jobs:
            jobname = job['fullname']
            print("Job",i,": ",jobname)
            i+=1
            #last build number:
            last_nr = self.lastBuildNr(jobname)
            self.printAllBuildsNumber(last_nr)
            for nr in range(1,last_nr+1):
                self.printBuildNumber(nr)
                self.printBuildDate(jobname,nr)
                self.printBuildWho(jobname,nr)
                self.printBuildState(jobname,nr)
            print()
        f = open(log_filename,"a")
        f.write("fetching data from Jenkins...\n" )
        f.close
    
    def lastBuildNr(self,jobname):
        jinfo = self.serverconn.get_job_info(jobname)
        if jinfo['lastCompletedBuild'] != None:
            lastbuildnumber = jinfo['lastCompletedBuild']['number']
        else:
            lastbuildnumber = 0
        return lastbuildnumber
    
    def printAllBuildsNumber(self,buildnumber):
        if buildnumber != 0:
            print("  Build amount: --- ",buildnumber," ---")
        else:
            print("  Build amount:  0 -- None builds done --")    
    
    def printBuildNumber(self,buildnumber):
        if buildnumber != 0:
            print("  Build: ",buildnumber)
        else:
            print("  Build:  0 -- None builds done --")
    
    def BuildDate(self,jobname,buildnumber):
        if buildnumber != 0:
            build = self.serverconn.get_build_info(jobname, buildnumber, depth=0)
            time_stamp = build['timestamp']/1000
            date_time = datetime.fromtimestamp(time_stamp)
            date_time = date_time.strftime("%m/%d/%Y, %H:%M:%S")
            return date_time
    
    def printBuildDate(self,jobname,buildnumber):
        if buildnumber != 0:
            print("  Buid date:", self.BuildDate(jobname, buildnumber))

    def BuildWho(self,jobname,buildnumber):
        if buildnumber != 0:
            build = self.serverconn.get_build_info(jobname, buildnumber, depth=0)
            return build['actions'][0]['causes'][0]['shortDescription']
    
    def printBuildWho(self,jobname,buildnumber):
        if buildnumber != 0:
            print(" ",self.BuildWho(jobname, buildnumber))
            
    def printBuildState(self,jobname,buildnumber):
        if buildnumber != 0:
            build = self.serverconn.get_build_info(jobname, buildnumber, depth=0)
            print(" ",build['result'])
    
    def buildState(self,jobname,buildnumber):
        if buildnumber !=0:
            build_res = self.serverconn.get_build_info(jobname, buildnumber, depth=0)['result']
            return build_res

    def coutSuccessJobs(self):
        jobs = self.serverconn.get_all_jobs()
        suc = 0
        fail = 0
        for job in jobs:
            jobname = job['fullname']
            last_nr = self.lastBuildNr(jobname)
            if last_nr != 0:
                build_res = self.serverconn.get_build_info(jobname, last_nr, depth=0)['result']
                if build_res =='SUCCESS':
                    suc +=1
                elif build_res == 'FAILURE':
                    fail +=1
        return suc, fail
    
    def printAllJobs(self, job_lista):
        print("Job id: |Job name:   |Build number: ")
        for job in job_lista:
            print("Job ",job['job_nr'],": ",job['job_name'])
            self.printBuildNumber(job['builds'])
            self.printBuildDate(job['job_name'], job['builds'])
            self.printBuildWho(job['job_name'], job['builds'])
            self.printBuildState(job['job_name'], job['builds'])
            print()
    
    
    def sortJobsByDateDesc(self,job_lista, iLow, iHigh):
        #jobs_list = self.AllJobs()
        #stop:
        if iLow >= iHigh or iLow <0 or iHigh <0:
            return
        compare_list = job_lista[iLow]
        lowersNumsEndIndex = iLow + 1
        for i in range(iLow+1,iHigh+1):
            if job_lista[i]['last_build_date'] == None:
                rob_list = job_lista[iHigh]
                job_lista[iHigh] = job_lista[i]
                job_lista[i] = rob_list
            if job_lista[i]['last_build_date'] != None and compare_list['last_build_date'] != None:
                if job_lista[i]['last_build_date'] >= compare_list['last_build_date']:
                    rob_list = job_lista[i]
                    job_lista[i] = job_lista[lowersNumsEndIndex]
                    job_lista[lowersNumsEndIndex] = rob_list
                    lowersNumsEndIndex += 1
        rob_list = job_lista[iLow]
        job_lista[iLow] = job_lista[lowersNumsEndIndex-1]
        job_lista[lowersNumsEndIndex-1] = rob_list
        self.sortJobsByDateDesc(job_lista, iLow, lowersNumsEndIndex-2)
        self.sortJobsByDateDesc(job_lista, lowersNumsEndIndex, iHigh)
        if lowersNumsEndIndex-2 <=0:
            f = open(log_filename,"a")
            f.write("data from Jenkins sorted by Date Desc...\n" )
            f.close 
        
    def sortJobsByBuildNrDesc(self,job_lista, iLow, iHigh):
        #jobs_list = self.AllJobs()
        #stop:
        if iLow >= iHigh or iLow <0 or iHigh <0:
            return
        compare_list = job_lista[iLow]
        lowersNumsEndIndex = iLow + 1
        for i in range(iLow+1,iHigh+1):
            if job_lista[i]['builds'] >= compare_list['builds']:
                rob_list = job_lista[i]
                job_lista[i] = job_lista[lowersNumsEndIndex]
                job_lista[lowersNumsEndIndex] = rob_list
                lowersNumsEndIndex += 1
        rob_list = job_lista[iLow]
        job_lista[iLow] = job_lista[lowersNumsEndIndex-1]
        job_lista[lowersNumsEndIndex-1] = rob_list
        self.sortJobsByBuildNrDesc(job_lista, iLow, lowersNumsEndIndex-2)
        self.sortJobsByBuildNrDesc(job_lista, lowersNumsEndIndex, iHigh)
        if lowersNumsEndIndex-2 <=0:
            f = open(log_filename,"a")
            f.write("data from Jenkins sorted by Build Number Desc...\n" )
            f.close         
    
    def changeNoneToStr(self, job_lista):
        for i in range(0,len(job_lista)):
            if job_lista[i]['last_build_date'] == None:
                job_lista[i]['last_build_date'] = {}
            if job_lista[i]['who_started_build'] == None:
                job_lista[i]['who_started_build'] = {}
            if job_lista[i]['success_build'] == None:
                job_lista[i]['success_build'] = {}
        return job_lista
    
    def printJsonFormat(self, job_lista):
        job_lista = self.changeNoneToStr(job_lista)
        print("{")
        print(" \"jobs\" : [")
        l = len(job_lista)
        for job in job_lista:
            l -= 1
            if l == 0:
                print("    ",job)
            else:
                print("    ",job,",")
            print()
        print(" ]")
        print()
        print("}")
        f = open(log_filename,"a")
        f.write("data from Jenkins displayed in JSon format...\n" )
        f.close 
    
    def changeFormat(self,job_lista):
        for i in range(0,len(job_lista)):
            job_lista[i] = str(job_lista[i])
            job_lista[i] = job_lista[i].replace('\"', ' ')
        return job_lista
        
    def saveToJsonFile(self, job_lista, filename):
        job_lista = self.changeNoneToStr(job_lista)
        job_lista = self.changeFormat(job_lista)
        f = open(filename,"w")
        f.write("{ \n" )
        f.write("\n")
        f.write(" \"jobs\" : [ \n")
        f.write("\n")
        l = len(job_lista)
        for job in job_lista:
            l -= 1
            rob = str(job)
            rob = rob.replace('\'', '\"')
            if l == 0:
                f.write("    ")     
                f.write(rob)
                f.write("\n")
            else:
                f.write("    ")
                f.write(rob)
                f.write(",\n")
            f.write("\n")
        
        f.write(" ] \n")
        f.write("\n")
        f.write("}")
        print("Data saved in file: ", filename)
        f.close
        f = open(log_filename,"a")
        f.write("data from Jenkins saved in file named: ")
        f.write(filename)
        f.write(" in JSon format...\n" )
        f.close 
    
    def changeStateToUnstableJSonFile(self,filename):
        if os.path.isfile(filename):
            f = open(filename,"r")
            job_lista = f.read()
            job_lista = job_lista.replace("SUCCESS", "UNSTABLE")
            job_lista = job_lista.replace("FAILURE", "UNSTABLE")
            f.close()
            f = open(filename,"w")
            f.write(job_lista)
            #print(job_lista)  
            f.close()
            print("change done - look into the file")
        else:
            print("File doesn't exists")
            sys.exit
              
    
config_file = 'my_config.ini'
log_filename = 'jenkins_conn_log.log'
print('Welcome in tool - for fetching and analysis data from Jenkins')
connection = JenkinsConnection(config_file,log_filename)
connection.getJenkinsCredentials()
#connection.connectToJenkins()
oper = JenkinsOperations(connection)
oper.printJobsAmount()

print('Choose what do you want to do:')
print('1 - show all the jobs with the last build done')
print('2 - show all the jobs with all the builds')
print('3 - sort descending by date')
print('4 - sort descending by build number')
print('5 - show all the jobs sorted by date')
print('6 - show all the jobs sorted by build number')
print('7 - show all jobs (you can sort them earlier by date or build number) JSON format on screen')
print('8 - show all jobs (you can sort them earlier by date or build number) in JSON format in a written json file')
print('9 - show the count of failed/ passed jobs')
print('10 - change in JSon file all \"failed\"/ \"success\" to \"unstable\"')
print('11 - close the program')
x = input('your choice: ')
i = 1
while not (x in ['1','2','3','4','5','6','7','8','9','10','11']):
    x = input('Make the correct choice again:')
    i += 1
    if i >= 5:
        exit    
if x == '1' :
    oper.printAllJobsLastBuildInfo()
elif x == '2':
    oper.printAllJobsInfo()
elif x == '3':
    job_lista = oper.AllJobs()
    oper.sortJobsByDateDesc(job_lista, 0, len(job_lista)-1)
    oper.printAllJobs(job_lista)
elif x == '4':
    job_lista = oper.AllJobs()
    oper.sortJobsByBuildNrDesc(job_lista, 0, len(job_lista)-1)
    oper.printAllJobs(job_lista)
elif x == '5':
    job_lista = oper.AllJobs()
    oper.sortJobsByDateDesc(job_lista, 0, len(job_lista)-1)
    oper.printAllJobs(job_lista)
elif x == '6':
    job_lista = oper.AllJobs()
    oper.sortJobsByBuildNrDesc(job_lista, 0, len(job_lista)-1)
    oper.printAllJobs(job_lista)
elif x == '7':
    job_lista = oper.AllJobs()
    odp = input('Do you want to sort it by date? (y/n): ')
    if odp == "Y" or odp == "y": 
        oper.sortJobsByDateDesc(job_lista, 0, len(job_lista)-1)
    else:
        odp = input('Do you want to sort it by build number? (y/n): ')
        if odp == "Y" or odp == "y": 
            oper.sortJobsByBuildNrDesc(job_lista, 0, len(job_lista)-1)
    oper.printJsonFormat(job_lista) 
elif x == '8':
    job_lista = oper.AllJobs()
    odp = input('Do you want to sort it by date? (y/n): ')
    if odp == "Y" or odp == "y": 
        oper.sortJobsByDateDesc(job_lista, 0, len(job_lista)-1)
    else:
        odp = input('Do you want to sort it by build number? (y/n): ')
        if odp == "Y" or odp == "y": 
            oper.sortJobsByBuildNrDesc(job_lista, 0, len(job_lista)-1)
    filename = 'jenkins_data.json'
    oper.saveToJsonFile(job_lista, filename)
elif x == '9':
    print("counting...")
    jobs_success = oper.coutSuccessJobs()[0]
    jobs_failed = oper.coutSuccessJobs()[1]
    print("Success jobs: ",jobs_success)
    print("Failed jobs: ", jobs_failed)
elif x == '10':
    print()
    filename = 'jenkins_data.json'
    oper.changeStateToUnstableJSonFile(filename)
elif x == '11':
    print('Program closed')
    exit
else:
    exit
        
