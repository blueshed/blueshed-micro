from tornado.template import Loader


def generate(template_path, *args, **kwargs):
    loader = Loader(template_path)
    for path in args:
        yield loader.load(path).generate(**kwargs).decode(encoding='UTF-8')
