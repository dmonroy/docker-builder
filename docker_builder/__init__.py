import os
import shutil
import subprocess
import tarfile
import tempfile
from docker import Client
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


class BuildCommand(object):

    @classmethod
    def from_yaml_file(cls, filepath):
        with open(filepath, 'r') as f:
            return cls(**yaml.load(f.read(), Loader))

    def get_client(self):
        return Client(base_url=os.getenv('DOCKER_HOST', 'unix://var/run/docker.sock'))

    def source_image_name(self):
        raise NotImplemented()

    def target_image_name(self):
        raise NotImplemented()

    def has_maintainer(self):
        return hasattr(self, 'maintainer') \
               or 'DOCKERFILE_MAINTAINER' in os.environ

    def get_maintainer(self):
        return getattr(self, 'maintainer', None) \
               or os.getenv('DOCKERFILE_MAINTAINER')

    def dockerfile_content(self):
        lines = []

        lines.append('FROM {}'.format(self.source_image_name()))

        if self.has_maintainer():
            lines.append('MAINTAINER {}'.format(self.get_maintainer()))

        for cmd in self.commands():
            lines.append(cmd)

        if self.exposed_ports():
            lines.append(
                'EXPOSE {}'.format(
                    ' '.join([str(port) for port in self.exposed_ports()])
                )
            )

        if self.entrypoint():
            lines.append('ENTRYPOINT {}'.format(str(self.entrypoint())))

        if self.cmd():
            lines.append('CMD {}'.format(str(self.cmd())))

        return '\n'.join(lines)

    def entrypoint(self):
        return None

    def cmd(self):
        return []

    def commands(self):
        return []

    def exposed_ports(self):
        return []

    def before_build(self):
        pass

    def after_build(self):
        pass

    def build(self, callback=None):
        success = True
        self.work_dir = tempfile.mkdtemp()
        self.before_build()
        image_name = self.target_image_name()
        dockerfile_path = os.path.join(self.work_dir, 'Dockerfile')

        with open(dockerfile_path, 'w') as dockerfile:
            dockerfile.write(self.dockerfile_content())

        c = self.get_client()
        for line in c.build(
            path=self.work_dir, stream=True, rm=True,
            pull=True, tag=image_name
        ):

            if callback is not None:
                callback(line)

        for line in c.push(image_name, stream=True):
            if callback is not None:
                callback(line)

        self.after_build()

        shutil.rmtree(self.work_dir)

        return success
