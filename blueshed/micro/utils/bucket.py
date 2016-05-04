import os
import boto
from boto.s3.key import Key


class AWSConfig(object):

    def __init__(self, key, secret):
        self.aws_access_key_id = key
        self.aws_secret_access_key = secret


class BucketException(Exception):
    pass

# because you cannot have dots in bucket name
# https://github.com/boto/boto/issues/2836
# import ssl
#
# _old_match_hostname = ssl.match_hostname
#
# def _new_match_hostname(cert, hostname):
#     if hostname.endswith('.s3.amazonaws.com'):
#         pos = hostname.find('.s3.amazonaws.com')
#         hostname = hostname[:pos].replace('.', '') + hostname[pos:]
#     if hostname.endswith('.s3-eu-west-1.amazonaws.com'):
#         pos = hostname.find('.s3-eu-west-1.amazonaws.com')
#         hostname = hostname[:pos].replace('.', '') + hostname[pos:]
#     return _old_match_hostname(cert, hostname)
#
# ssl.match_hostname = _new_match_hostname


class Bucket(object):
    '''
        Useful wrapper to boto bucket
    '''
    
    def __init__(self, s3, name, bucket):
        self.s3 = s3
        self.name = name
        self._bucket = bucket

    @classmethod
    def get_buckets(cls, aws_config):
        s3 = boto.connect_s3(aws_config.aws_access_key_id,
                             aws_config.aws_secret_access_key)
        return [cls(s3, b.name, b) for b in s3.get_all_buckets()]

    @classmethod
    def get_bucket_by_name(cls, aws_config, name):
        s3 = boto.connect_s3(aws_config.aws_access_key_id,
                             aws_config.aws_secret_access_key)
        b = s3.get_bucket(name)
        return cls(s3, b.name, b)

    @classmethod
    def create(cls, aws_config, name):
        s3 = boto.connect_s3(aws_config.aws_access_key_id,
                             aws_config.aws_secret_access_key)
        b = s3.create_bucket(name)
        return cls(s3, b.name, b)

    @property
    def bucket(self):
        if self._bucket is None:
            raise BucketException("Bucket {} deleted".format(self.name))
        return self._bucket

    def list(self):
        return self.bucket.list()

    def empty(self):
        for key in self.bucket.get_all_keys():
            self.bucket.delete_key(key)

    def delete(self):
        self.empty()
        self.bucket.delete()
        self._bucket = None

    def add(self, data=None, filepath=None, key=None, meta=None):
        assert(data or filepath)
        if filepath is not None and key is None:
            key = os.path.split(filepath)[-1]
        k = Key(self.bucket, key)
        if meta:
            for m, v in meta.items():
                k.set_metadata(m, v)
        if filepath:
            k.set_contents_from_filename(filepath)
        else:
            k.set_contents_from_string(data)
        k.set_acl('public-read')
        return k.name

    def get(self, key, file=None):
        k = self.bucket.get_key(key)
        if file:
            k.get_contents_to_file(file)
        else:
            return k.get_contents_as_string()

    def gen_url(self, keyname):
        return "http:{}".format(self.get_abs_url(keyname))

    def gen_abs_url(self, keyname):
        '''
            return a url without protocol to the resource
        '''
        return "//{}.{}/{}".format(self.name, self._bucket.connection.host, keyname)
