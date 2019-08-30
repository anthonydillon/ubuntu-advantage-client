from uaclient.clouds import aws
from uaclient import exceptions
from uaclient import util
from uaclient import clouds

CLOUD_INSTANCE_MAP = {
    'ec2': aws.UAPremiumAWSInstance, 'aws': aws.UAPremiumAWSInstance}

DS_PICKLE_FILE = '/var/lib/cloud/instance/obj.pkl'


@util.retry(FileNotFoundError, [1, 2])
def get_cloud_type_from_datasource_pickle(pkl_file=DS_PICKLE_FILE) -> str:
    with open(pkl_file, 'rb') as stream:
        py2_pickle_content = stream.read()
    DATASOURCE_MATCH = b'DataSource'
    for py2_pickle_var in py2_pickle_content.split(b'\n')[0:6]:
        if DATASOURCE_MATCH in py2_pickle_var:
            if py2_pickle_var[:len(DATASOURCE_MATCH)] != DATASOURCE_MATCH:
                continue
            ds_classname = py2_pickle_var[len(DATASOURCE_MATCH):].decode()
            return ds_classname.lower().replace('datasource', '')
    return None


def get_cloud_type() -> str:
    if util.which('cloud-id'):
        # Present in cloud-init on >= Xenial
        out, _err = util.subp(['cloud-id'])
        return out.strip()
    try:
        return get_cloud_type_from_datasource_pickle()
    except FileNotFoundError:
        return 'unknown: no detected datasource yet'
    return ''


def cloud_instance_factory() -> clouds.UAPremiumCloudInstance:
    cloud_type = get_cloud_type()
    if not cloud_type:
        raise exceptions.UserFacingError(
            'Could not determine cloud type UA Premium Images.'
            ' Unable to attach')
    cls = CLOUD_INSTANCE_MAP.get(cloud_type)
    if not cls:
        raise exceptions.UserFacingError(
            "No UAPremiumCloudInstance class available for cloud type '%s'" %
            cloud_type)
    instance = cls()
    if not instance.is_viable:
        raise exceptions.UserFacingError(
            'This vm is not a viable premium image on cloud "%s"' % cloud_type)
    return instance
