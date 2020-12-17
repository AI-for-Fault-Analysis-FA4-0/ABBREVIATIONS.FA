# -*- coding: utf-8 -*-
"""
Created on Tue Dec 15 07:15:38 2020

@author: emse
"""

import re
import fitz
import string
import numpy as np
from os.path import join
import pandas as pd
from itertools import chain #recurssive list flatening...
from tika import parser #extract text from pdf

pdf_path = 'C:\\Users\\emse\\Documents\\FA4.0\Houari'

path = {'data': 'C:\\Users\\emse\\Documents\\FA4.0\\Mireille\\Donnes\\hdf5', #hdf5 database
        'utils': 'C:\\Users\\emse\\Documents\\FA4.0\\kenneth\\Scripts\\utils' #kenneth utils
        }

#import stopwords
with open(join(path['utils'], 'stopwords.txt'), 'r+',encoding="utf8") as st:
    stopwords = set([x for x in st.read().split()]) #mix of Italia, English and French words...
        


# text = np.load(join(path['data'], 'book_mine\\fa_houari.npy'), allow_pickle=True)
# text = list(np.atleast_1d(text))[0]
# text = text.replace('\n', ' ')

class AbbreviationMiner(object):
    '''AbbreviationMiner is used for extracting abbreviations in the Wiley book:
        
        'Failure Analys is : A Practical Guide for Manufacturers of Electronic Components and Systems , First Edition.
        Marius I. Bazu and Titu-Marius I. Bajenescu.
        © 2011 John Wiley & Sons, Ltd. P ublis hed 2011 by John Wiley & Sons , Ltd. ISBN: 978-0-470-74824-4'
        
        Source: https://www.wiley.com/en-us/Failure+Analysis%3A+A+Practical+Guide+for+Manufacturers+of+Electronic+Components+and+Systems-p-9781119990000
        
        
        
    '''
    def __init__(self, stopword = None):
        '''
        

        Parameters
        ----------
        stopword : list, optional
            English stopwords. The default is None.

        Returns
        -------
        None.

        '''
        if not stopword:
            stopword = stopwords
            self.stopwords = stopword
        else:
            self.stopwords = stopword
        return
    
    def remove_hyp_uds(self, text:str):
            '''
            
    
            Parameters
            ----------
            text : str
                text for which we want to remove hyphens and underscore.
    
            Returns
            -------
            str
                string without hyphen and underscore.
    
            '''
            text_ls = list(chain(*[x.split('-') for x in text.split('_')])) #remove and underscore
            text_ls = ' '.join(text_ls)
            text_ls =  text_ls.split('/') #check if there are any forward slashes
            return ' '.join(text_ls)
        
    def remove_specific_characters(self, text:str):
            '''
            
    
            Parameters
            ----------
            text : str
                text.
    
            Returns
            -------
            str
                text without punctuations.
    
            '''
            spec = text.replace('.', '').replace(',', '').replace('–', '').replace('•', '').replace('©', '').replace('◦C', '').\
                    replace('&', '').replace(':', '').replace(';', '').replace('>', '').replace('<', '')
            return spec
    
    
    def remove_stopwords(self, text:str):
        '''
        

        Parameters
        ----------
        text : str
            string:text.

        Returns
        -------
        str
            text/sentence after stopword removal.

        '''
        toks = [x.strip() for x in text.split(' ')]
        while toks[0] in self.stopwords:
            if len(toks) > 1:
                toks = toks[1:]
            elif len(toks) == 1:
                return ' '
        else:
            return ' '.join(toks)
    
    
    def check_upper_higher_than_lower(self, text:str):
        '''Check the size of Capitalization present 
            in a token
        

        Parameters
        ----------
        text : str
            text/sentences.

        Returns
        -------
        bool
            True/False.

        '''
        ck = [x.isupper() for x in text]
        upper, lower = ck.count(True), ck.count(False) #return frequency counts
        if any(ck):
            return True
        elif any(ck):
            return False
        elif upper > lower:
            return True
        elif upper == lower:
            return True
        else:
            return False
    
    
    
    def method_scrap_all(self, filename:str = None):
        '''
        

        Parameters
        ----------
        filename : str, optional
            Filename (as seen on local machine). The default is None.

        Returns
        -------
        None.

        '''
        if filename == None:
            filename = 'fa_houari.pdf'
            self.filename = filename
        raw = parser.from_file(join(pdf_path, self.filename))
        text = raw['content']
        text = text.replace('\n', ' ')
        #--technique one for extracting abbreviation and meaning extraction
        self.kv = {}
        txt = self.remove_specific_characters(self.remove_hyp_uds(text))
        self.tok = [x for x in txt.split(' ') if not x == '' if not x == ' ' if not x.isdigit()]
        for enum, ii in enumerate(self.tok):
            if ii.strip()[0] == '(' and ii.strip()[-1] == ')':
                abb, tmp_tt = ii.strip('()'), len(ii.strip('()')) #remove braces and check length of word
                if not abb.isdigit() and len(abb) < 6 or self.check_upper_higher_than_lower(abb):
                    self.tt_af = ' '.join(self.tok[(enum-tmp_tt):enum]).replace("'", "")
                    self.tt_af = re.sub(r"[\(\[].*?[\)\]]", '',self.tt_af).replace("'", '')
                    self.tt_af = re.sub(r"[\(\[].", '',self.tt_af).replace("'", '')
                    self.tt_af = re.sub(r".*?[\)\]]", '',self.tt_af).replace("'", '')
                    self.tt_af = self.tt_af.replace("'", '').replace("‘", '').replace("’", '')
                    self.tt_ff = self.remove_stopwords(' '.join(x for x in self.tt_af.split(' ') if not x == ''))
                    if '%' in abb:
                        if len(abb) == 1:
                            self.kv[f'{abb}'] = self.tt_ff
                    else:
                        if abb[0] == 'X' and len(abb[:3]) > 1:
                            if not self.tt_ff[:1] == 'x':
                                self.kv[f'{abb}'] = 'x-' + self.tt_ff
                            else:
                                self.kv[f'{abb}'] = self.tt_ff
                        else:
                            self.kv[f'{abb}'] = self.tt_ff
                    
                    
    def method_scrap_acronym(self):
        '''
        

        Returns
        -------
        None.

        '''
        #---technique two for extracting tables only...      
        pf_rng = np.arange(310, 318) #acronym pages in FA book
        pdfr = fitz.open(join(pdf_path, 'fa_houari.pdf'))
        
        abt = {}
        for ij in pf_rng:
            pg = pdfr[int(ij)]
            self.txt = pg.getText('text').split('\n')
            self.punct = string.punctuation
            for enum, ii in enumerate(self.txt):
                #skip acronym row
                if not ii == 'Acronyms':
                    #chek if the first index is in upper case
                    if ii.isupper():
                        #check the the index that follows it is lower case (or atleast, mostly lowercase)
                        if not self.txt[enum+2].strip('-').strip('()').strip(';').isupper():
                            pp = ' '.join(x for x in self.txt[enum+2].strip('-').split(';'))
                            #remove punctuations before appending...
                            if not any(list(map(lambda x: x in self.punct, pp))):
                                cc  = self.txt[enum+1] +' '+ self.txt[enum+2].split(';')[0]
                                abt[f'{ii}'] = cc
                            else:
                                abt[f'{ii}'] = self.txt[enum+1]
                        else:
                            abt[f'{ii}'] = self.txt[enum+1]
                    else:
                        pass
                else:
                    pass
        
        
        '''compare both methods/results and update global abbr. with acronym.
            This is because the acronym page contains most but not all abbreviations; but the
            general scrapping collects all abbreviations with an error likelihood.
        '''
        try:
            for ii, ij in self.kv.items():
                for p, q in abt.items():
                    #udpate global scrapping abbreviations with acronym and capitalize first letters
                    q = q.strip(',').strip('.')
                    self.kv[f'{p}'] = q
            for ii, ij in self.kv.items():
                self.kv[f'{ii}'] = ij.title() #capitaliza first characters of every word
        #runtime error flags when extending the length of a dictionay. Its just a check
        #no worries.
        except RuntimeError:
            pass
        

    def pascal_update(self):
        '''
        

        Returns
        -------
        None.

        '''
        #update abbreviations with pascal abbreviations..
        with open(join(path['utils'], 'pascal_abb.txt'), 'r+') as st:
            self.pas = st.read().split('\t\t')
        
        self.pas = [w.replace('\t', '').split('\n') for w in self.pas]
        self.pas = [w.replace('=', '').strip() for w in list(chain(*self.pas)) if not w == '']
        
        self.kw = {}
        for enum, ii in enumerate(self.pas):
            '''For abbreviations with lowercase; we check that the number of 
                uppercase is higher than the number of lowercase'''
            if ii.isupper() or len(ii) == 2 or self.check_upper_higher_than_lower(ii) and len(ii) < 6:
                self.kw[f'{ii}'] = re.sub(r"[\(\[].*?[\)\]]", '', self.pas[enum+1])
        
        #update major dictionary/abbrv with pascal abbreviations
        try:
            for ii, ij in self.kv.items():
                for p, q in self.kw.items():
                    q = q.strip(',').strip('.')
                    self.kv[f'{p}'] = q
        except RuntimeError:
            pass
        
    
    def preprocess_final(self):
        self.method_scrap_all()
        self.method_scrap_acronym()
        self.pascal_update()
        #preprocess updated abbreviations and meaning...
        ddt = pd.DataFrame({'abbreviations': list(self.kv.keys()), 'meaning': list(self.kv.values())})
        ddt = ddt[ddt.meaning != ' ']
        ddt = ddt.sort_values(by = 'abbreviations')
        ddt.index = np.arange(ddt.shape[0])
        ddt = ddt.iloc[:800, :]
        return ddt

#ddt.to_csv(join(path['data'], "abbr\\abbreviations.csv"), index = False, sep = ';')

#%%
if __name__ == '__main__':
    
    abbr = AbbreviationMiner().preprocess_final()




