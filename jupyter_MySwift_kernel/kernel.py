##//%file:kernel.py
#
#   MyPython Jupyter Kernel
#
from math import exp
from queue import Queue
from threading import Thread
from ipykernel.kernelbase import Kernel
from pexpect import replwrap, EOF
from jinja2 import Environment, PackageLoader, select_autoescape,Template
from abc import ABCMeta, abstractmethod
from typing import List, Dict, Tuple, Sequence
from shutil import copyfile,move
from urllib.request import urlopen
import socket
import copy
import mmap
import contextlib
import atexit
import platform
import atexit
import base64
import urllib.request
import urllib.parse
import pexpect
import signal
import typing 
import typing as t
import re
import signal
import subprocess
import tempfile
import os
import stat
import sys
import traceback
import os.path as path
import codecs
import time
import importlib
import importlib.util
import inspect
from . import ipynbfile
from plugins import ISpecialID
# from plugins.ISpecialID import IStag,IDtag,IBtag,ITag,ICodePreproc
from plugins._filter2_magics import Magics
from .Mymacroprocessor import Mymacroprocessor
try:
    zerorpc=__import__("zerorpc")
    # import zerorpc
except:
    pass
fcntl = None
msvcrt = None
bLinux = True
if platform.system() != 'Windows':
    fcntl = __import__("fcntl")
    bLinux = True
else:
    msvcrt = __import__('msvcrt')
    bLinux = False
from .MyKernel import MyKernel
class MySwiftKernel(MyKernel):
    implementation = 'jupyter-MySwift-kernel'
    implementation_version = '1.0'
    language = 'swift'
    language_version = ''
    language_info = {'name': 'swift',
                     'version': sys.version.split()[0],
                     'mimetype': 'text/swift',
                     'codemirror_mode': {
                        'name': 'ipython',
                        'version': sys.version_info[0]
                     },
                     'pygments_lexer': 'ipython%d' % 3,
                     'nbconvert_exporter': 'Swift',
                     'file_extension': '.ts'}
    runfiletype='script'
    banner = "MySwift kernel.\n" \
             "Uses Swift, creates source code files and executables in temporary folder.\n"
    kernelinfo="[MySwift kernel]"
    main_head = "\n" \
            "\n" \
            "int main(List<String> arguments){\n"
    main_foot = "\nreturn 0;\n}"
##//%include:src/comm_attribute.py
    def __init__(self, *args, **kwargs):
        super(MySwiftKernel, self).__init__(*args, **kwargs)
        self.runfiletype='script'
        self.kernelinfo="[MySwiftKernel{0}]".format(time.strftime("%H%M%S", time.localtime()))
        
#################
    def compile_with_swiftc(self, source_filename, binary_filename, cflags=None, ldflags=None,env=None,magics=None):
        # cflags = ['-std=c89', '-pedantic', '-fPIC', '-shared', '-rdynamic'] + cflags
        # cflags = ['-std=c99', '-Wdeclaration-after-statement', '-Wvla', '-fPIC', '-shared', '-rdynamic'] + cflags
        # cflags = ['-std=iso9899:199409', '-pedantic', '-fPIC', '-shared', '-rdynamic'] + cflags
        # cflags = ['-std=c99', '-pedantic', '-fPIC', '-shared', '-rdynamic'] + cflags
        # cflags = ['-std=c11', '-pedantic', '-fPIC', '-shared', '-rdynamic'] + cflags
        outfile=binary_filename
        orig_cflags=cflags
        orig_ldflags=ldflags
        # if self.linkMaths:
        #     cflags = cflags + ['-lm']
        # if self.wError:
        #     cflags = cflags + ['-Werror']
        # if self.wAll:
        #     cflags = cflags + ['-Wall']
        # if self.readOnlyFileSystem:
        #     cflags = ['-DREAD_ONLY_FILE_SYSTEM'] + cflags
        # if self.bufferedOutput:
        #     cflags = ['-DBUFFERED_OUTPUT'] + cflags
        index=0
        for s in cflags:
            if s.startswith('-o'):
                if(len(s)>2):
                    outfile=s[2:]
                    del cflags[index]
                else:
                    outfile=cflags[cflags.index('-o')+1]
                    if outfile.startswith('-'):
                        outfile=binary_filename
                    del cflags[cflags.index('-o')+1]
                    del cflags[cflags.index('-o')]
            binary_filename=outfile
            index+=1
        args=[]
        if magics!=None and len(self.mymagics.addkey2dict(magics,'ccompiler'))>0:
            args = magics['ccompiler'] + orig_cflags +[source_filename] + orig_ldflags
        else:
            args = ['swiftc', source_filename] + ['-o', binary_filename]+ cflags  + ldflags
        # self._log(''.join((' '+ str(s) for s in args))+"\n")
        return self.mymagics.create_jupyter_subprocess(args,env=env,magics=magics),binary_filename,args
    def _exec_swiftc_(self,source_filename,magics):
        self.mymagics._logln('Generating executable file')
        with self.mymagics.new_temp_file(suffix='.out') as binary_file:
            magics['status']='compiling'
            p,outfile,gcccmd = self.compile_with_swiftc(
                source_filename, 
                binary_file.name,
                self.mymagics.get_magicsSvalue(magics,'cflags'),
                self.mymagics.get_magicsSvalue(magics,'ldflags'),
                self.mymagics.get_magicsbykey(magics,'env'),
                magics=magics)
            returncode=p.wait_end(magics)
            p.write_contents()
            magics['status']=''
            binary_file.name=os.path.join(os.path.abspath(''),outfile)
            if returncode != 0:  # Compilation failed
                self.mymagics._logln(''.join((str(s) for s in gcccmd))+"\n",3)
                self.mymagics._logln("C compiler exited with code {}, the executable will not be executed".format(returncode),3)
                # delete source files before exit
                os.remove(source_filename)
                os.remove(binary_file.name)
        return p.returncode,binary_file.name
##do_runcode
    def do_runcode(self,return_code,file_name,magics,code, silent, store_history=True,
                    user_expressions=None, allow_stdin=True):
        return_code=return_code
        file_name=file_name
        bcancel_exec=False
        retinfo=self.mymagics.get_retinfo()
        retstr=''
        ##代码运行前
        p = self.mymagics.create_jupyter_subprocess([file_name]+ magics['_st']['args'],cwd=None,shell=False,env=self.mymagics.addkey2dict(magics,'env'),magics=magics)
        #p = self.create_jupyter_subprocess([binary_file.name]+ magics['args'],cwd=None,shell=False)
        #p = self.create_jupyter_subprocess([self.master_path, binary_file.name] + magics['args'],cwd='/tmp',shell=True)
        self.mymagics.g_rtsps[str(p.pid)]=p
        return_code=p.returncode
        ##代码启动后
        bcancel_exec,retstr=self.mymagics.raise_plugin(code,magics,return_code,file_name,3,2)
        # if bcancel_exec:return bcancel_exec,retinfo,magics, code,file_name,retstr
        
        if len(self.mymagics.addkey2dict(magics,'showpid'))>0:
            self.mymagics._write_to_stdout("The process PID:"+str(p.pid)+"\n")
        return_code=p.wait_end(magics)
        # del self.mymagics.g_rtsps[str(p.pid)]
        # p.write_contents(magics)
        ##
        ##调用接口
        return_code=p.returncode
        ##代码运行结束
        if p.returncode != 0:
            self.mymagics._log("Executable exited with code {}".format(p.returncode),2)
        return bcancel_exec,retinfo,magics, code,file_name,retstr
##do_compile_code
    def do_compile_code(self,return_code,file_name,magics,code, silent, store_history=True,
                    user_expressions=None, allow_stdin=True):
        return_code=0
        file_name=file_name
        sourcefilename=file_name
        bcancel_exec=False
        retinfo=self.mymagics.get_retinfo()
        retstr=''
        returncode,binary_filename=self._exec_swiftc_(file_name,magics)
        file_name=binary_filename
        return_code=returncode
        
        if returncode!=0:return  True,retinfo, code,file_name,retstr
        return bcancel_exec,retinfo,magics, code,file_name,retstr
##do_create_codefile
    def do_create_codefile(self,magics,code, silent, store_history=True,
                    user_expressions=None, allow_stdin=True):
        return_code=0
        file_name=''
        bcancel_exec=False
        retinfo=self.mymagics.get_retinfo()
        retstr=''
        source_file=self.mymagics.create_codetemp_file(magics,code,suffix='.swift')
        newsrcfilename=source_file.name
        file_name=newsrcfilename
        return_code=True
        return bcancel_exec,self.mymagics.get_retinfo(),magics, code,file_name,retstr
##do_preexecute
    def do_preexecute(self,code,magics,silent, store_history=True,
                user_expressions=None, allow_stdin=False):
        bcancel_exec=False
        retinfo=self.mymagics.get_retinfo()
        
        return bcancel_exec,retinfo,magics, code
