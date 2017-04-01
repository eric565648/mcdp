from contracts import contract
import os
from contracts.utils import indent

class ProxyDirectory(object):
    
    @contract(files='dict(str:*)|None', directories='dict(str:*)|None')
    def __init__(self, files=None, directories=None):
        if files is None:
            files = {}
        if directories is None:
            directories = {}
        self.files = files
        self.directories = directories
    
    def __len__(self):
        return len(self.files) + len(self.directories)
    
    def __getitem__(self, key):
        if key in self.files:
            return self.files[key]
        if key in self.directories:
            return self.directories[key]
        raise KeyError(key)
    
    def __setitem__(self, key, x):
        if isinstance(x, ProxyDirectory):
            self.directories[key] =x
        elif isinstance(x, ProxyFile):
            self.files[key] =x
        else:
            msg = 'Cannot set key %r to %r' % (key, x)
            raise ValueError(msg)
    
    def __iter__(self):
        for x in self.files:
            yield x
        for x in self.directories:
            yield x
            
    def items(self):
        for x in self.files.items():
            yield x
        for x in self.directories.items():
            yield x
            
    def to_disk(self, base):
        
        if not os.path.exists(base):
            os.makedirs(base)
            
        for filename, proxy_file in self.files.items():
            fn = os.path.join(base, filename)
            proxy_file.to_disk(fn)
        
        for dirname, proxy_dir in self.directories.items():
            d = os.path.join(base, dirname)
            proxy_dir.to_disk(d)                
    
    @staticmethod
    def from_disk(base):
        d0 = ProxyDirectory()
        for fn in os.listdir(base):
            full = os.path.join(base, fn)
            if os.path.isdir(full):
                d0[fn] = ProxyDirectory.from_disk(full)
            else:
                d0[fn] = ProxyFile.from_disk(full)
        return d0
    
    def tree(self):
        s = ''
        for k in sorted(self.files):
            f = self.files[k]
            MAX = 20
            if len(f.contents) < MAX:
                s += '%s = %r\n' % (k, f.contents)
            else:
                s += '%s: %d bytes\n' % (k, len(f.contents))
        for k in sorted(self.directories):
            d = self.directories[k]
            s += '%s/\n' % k
            s += indent(d.tree().rstrip(), '.   ') + '\n' 
        return s


class ProxyFile(object):
    @contract(contents=str)
    def __init__(self, contents):
        self.contents = contents
        
    @staticmethod
    def from_disk(fn):
        with open(fn, 'r') as f:
            contents = f.read()
        return ProxyFile(contents)
    
    def to_disk(self, fn):
        dn = os.path.dirname(fn)
        if not os.path.exists(dn):
            os.makedirs(dn)
        with open(fn, 'w') as f:
            f.write(self.contents)
        
        