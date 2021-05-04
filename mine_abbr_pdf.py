# -*- coding: utf-8 -*-
"""
Created on Tue Dec 15 07:15:38 2020

@author: emse
"""
###############################################################################
#MIT License
#
#Copyright (c) 2021 AI for Fault Analysis FA4.0
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
################################################################################


import re
import fitz
import string
import numpy as np
from os.path import join
import pandas as pd
from itertools import chain #recursive list flatening...
from tika import parser #extract text from pdf

pdf_path = '/home/ifeanyi.ezukwoke/Documents/FA4.0/Houari'

paths = {'data': '.../Donnes/hdf5', #hdf5 database
        'utils': '.../Scripts/utils' #kenneth utils
        }

#import stopwords
with open(join(paths['utils'], 'stopwords.txt'), 'r+',encoding="utf8") as st:
    stopwords = set([x for x in st.read().split()]) #mix of Italia, English and French stop words...
        


# text = np.load(join(path['data'], 'book_mine\\fa_houari.npy'), allow_pickle=True)
# text = list(np.atleast_1d(text))[0]
# text = text.replace('\n', ' ')

class AbbreviationMiner(object):
    '''AbbreviationMiner is used for extracting abbreviations in the Wiley book:
        
        'Failure Analysis : A Practical Guide for Manufacturers of Electronic Components and Systems, First Edition.
        Marius I. Bazu and Titu-Marius I. Bajenescu.
        © 2011 John Wiley & Sons, Ltd. Publis hed 2011 by John Wiley & Sons, Ltd. ISBN: 978-0-470-74824-4'
        
        Source: https://www.wiley.com/en-us/Failure+Analysis%3A+A+Practical+Guide+for+Manufacturers+of+Electronic+Components+and+Systems-p-9781119990000
        
        
        
    '''
    def __init__(self, stopword = None, path:str = None):
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
        if not path:
            path = paths
            self.path = path
        else:
            self.path = path
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
        elif not any(ck):
            return False
        elif upper > lower:
            return True
        elif upper == lower:
            return True
        else:
            return False
    
    
    def check_file_ext(self, filename):
        '''Check file extension
        

        Parameters
        ----------
        filename : str
            file name.

        Raises
        ------
        ValueError
            DESCRIPTION.

        Returns
        -------
        None.

        '''
        self.filename = filename
        if not self.filename[-3:] == 'txt':
            raise ValueError(f'{self.filename} not a text file.\nFile extension should be a .txt format')
        else:
            return True
    
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
        else:
            self.filename = filename
            assert self.check_file_ext(self.filename) == True, 'something went wrong'
            with open(join(self.path['data'], self.filename), 'r+', encoding = "utf8") as st:
                text = st.read()
            text = text.replace('\n', ' ')
        #--technique one for extracting abbreviation and meaning extraction
        self.kv = {}
        txt = self.remove_specific_characters(self.remove_hyp_uds(text))
        self.tok = [x for x in txt.split(' ') if not x == '' if not x == ' ' if not x.isdigit()]
        for enum, ii in enumerate(self.tok):
            if len(ii) > 2:
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
                                self.kv[f'{abb}'] = self.tt_ff.title()
                    
    
    def method_scrap_acronym(self, filename:str = None):
        '''
        

        Returns
        -------
        None.

        '''
        if filename == None:
            filename = 'fa_houari.pdf'
            self.filename = filename
        else:
            self.filename = filename
        #---technique two for extracting tables only...      
        pf_rng = np.arange(310, 318) #acronym pages in FA book
        pdfr = fitz.open(join(pdf_path, self.filename))
        
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
        with open(join(self.path['utils'], 'pascal_abb.txt'), 'r+', encoding='windows-1252') as st:
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
        
    
    def preprocess_final(self, slice_:int = None, filename:str = None):
        if not slice_:
            slice_ = 1000
            self.slice_ = slice_
        else:
            self.slice_ = slice_
        if not filename:
            filename = 'fa_houari.pdf'
            self.filename = filename
        else:
            self.filename = filename
        self.method_scrap_all(filename = self.filename)
        self.method_scrap_acronym()
        self.pascal_update()
        #preprocess updated abbreviations and meaning...
        ddt = pd.DataFrame({'Abbreviations': list(self.kv.keys()), 'Meaning': list(self.kv.values())})
        ddt = ddt[ddt.Meaning != ' ']
        ddt = ddt.sort_values(by = 'Abbreviations')
        ddt.index = np.arange(ddt.shape[0])
        ddt = ddt.iloc[:slice_, :]
        return ddt



#%%
if __name__ == '__main__':
    
    #--Section A: this section mines abbreviation fro Wiley book
    #abbr = AbbreviationMiner().preprocess_final(filename = 'fa_houari.txt')
    #abbr.to_csv(join(paths['data'], "abbr/abbreviations_up.csv"), index = False, sep = ';') #unprocessed abbreviations...
    
    #---Section B: mines abbreviation from MC --> You need to comment this section to run the first section and vice-versa
    #----Update the abbreviations with Maltiel Consulting
    '''Maltiel Consulting Abbreviations
    Source: http://maltiel-consulting.com/Semiconductor_Technology_Acronyms_List_maltiel_consulting.htm#B
    '''
    
    kw = {}
    with open(join(paths['utils'], 'semi_a.txt'), 'r+', encoding='utf-8') as st:
        pas = st.readlines()
    
    abbr = pd.read_csv(join(paths['data'], 'abbr/abbreviations.csv'), sep = ',')
    for ii in np.array(abbr):
        kw[f'{ii[0]}'] = ii[1]
    
    for enum, ii in enumerate(pas):
        aa_ii = ii.split(',')
        if len(aa_ii) > 1:
            kw[f'{aa_ii[0]}'] = aa_ii[1].strip().title()
    mc = pd.DataFrame({'Abbreviations': list(kw.keys()), 'Meaning': list(kw.values())})
    mc = mc[mc.Meaning != ' ']
    mc = mc.sort_values(by = 'Abbreviations')
    mc.index = np.arange(mc.shape[0])
    mc.to_csv(join(paths['data'], "abbr/Abbreviation_complete.csv"), index = False, sep = ';')
    
    
    
    
    
    
    
    
