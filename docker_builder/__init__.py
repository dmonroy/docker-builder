import os
import shutil
import subprocess
import tempfile
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
        return ['/bin/sh']

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

    def build(self):
        success = True
        self.work_dir = tempfile.mkdtemp()
        self.before_build()

        dockerfile_path = os.path.join(self.work_dir, 'Dockerfile')

        with open(dockerfile_path, 'w') as dockerfile:
            dockerfile.write(self.dockerfile_content())

        try:
            subprocess.check_call(
                ["docker", "build", "-t", self.target_image_name(), self.work_dir]
            )
        except subprocess.CalledProcessError:
            success = False

        self.after_build()

        shutil.rmtree(self.work_dir)

        return success
