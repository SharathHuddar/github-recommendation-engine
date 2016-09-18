import pymongo, csv
from pymongo import MongoClient
from github3 import login as glin
from github3 import iter_user_repos
from bson.json_util import dumps
import numpy as np


client = MongoClient()
db = client.github
users = db.users
users.ensure_index('username',unique=True)
languages_list = ['', 'Shell', 'Java', 'HTML', 'Python', 'JavaScript', 'CSS', 'C']

def build_model(user):
    #with open('languages.csv','rb') as f:
        #reader = csv.reader(f)
        #languages_list = list(reader)
    languages_list = ['', 'Shell', 'Java', 'HTML', 'Python', 'JavaScript', 'CSS', 'C']
    client = MongoClient()
    db = client.github
    repositories = db.repositories
    repoTable = np.empty((0,len(languages_list)))
    for repo in repositories.find():
        langArray = np.empty(len(languages_list))
        #langArray[0] = repo['repoName']
        i=0
        for language in languages_list:

            for key,value in repo['languages'].items():
                if key == language:
                    langArray[i]=value
            i=i+1
        np.append(repoTable,langArray)
        print langArray

    print repoTable
    np.savetxt("out.csv",repoTable,delimiter= ',')



def insert_train_data(user):
    kill = 0
    KILL = 2
    client = MongoClient()
    db = client.github
    repositories = db.repositories
    for f in user.iter_followers():
        if kill == KILL:
            break
        user2=user.user(f)
        follower_followeres = (list(user2.iter_followers()))
        for ff in follower_followeres:
            if kill == KILL:
                break
            user3 = user.user(ff)

            repo = list(user.iter_user_repos(user3))
            for rep in repo:
                kill = kill + 1
                print 'repo:', kill
                if kill == KILL:
                    break
                languages = list(rep.iter_languages())
                summ=0
                dictrepo = {
                    "repoName" : rep.full_name,
                    "languages":{}
                }
                for l in languages:
                    if l[0] in languages_list:
                            summ=summ+int(l[1])

                langs = {}
                for locallangs in languages_list:
                    for l in languages:
                        if l[0]==locallangs:

                            langs.update({l[0]:str(l[1]/float(summ))})
                        else:
                            langs.update({locallangs:str(0)})
                dictrepo["languages"] = langs
                repositories.insert_one(dictrepo)
    build_model(user)

def insert_repos(user, repos):
    username = user.user().login
    dictRepos = {}
    dictLang = {}
    for r in repos:
        #print r.full_name
        repo = {
            r.full_name:{

            }
        }
        languages = list(r.iter_languages())
        sum=0
        Lang = {}
        for l in languages:
            sum=sum+int(l[1])
        for l in languages:
            Lang = {l[0]:float(l[1])/sum}
            dictLang.update(Lang)
        repo[r.full_name] = dictLang
        dictLang = {}
        #print repo
        dictRepos.update(repo)
    users.update({'username':username},{'username':username,'repos':dictRepos} , True)
    insert_train_data(user)



def create_user_profile(user):
    client = MongoClient()
    db = client.github
    users = db.users

    try:
        users.insert_one({'username':user.user().login})
    except:
        pass
    repos = list(user.iter_user_repos(user.user()))
    insert_repos(user,repos)
