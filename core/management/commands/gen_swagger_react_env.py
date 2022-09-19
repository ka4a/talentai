import json
import collections
from distutils.util import strtobool

from drf_yasg.management.commands.generate_swagger import Command as SwaggerBaseCommand
from drf_yasg.codecs import OpenAPICodecJson


def strip_data(spec):
    spec['info']['title'] = ''

    for _, value in spec['paths'].items():
        for key, data in value.items():
            if key == 'parameters':
                for p in data:
                    p.pop(
                        'description', None
                    )  # ['paths'][PATH]['parameters'][X]['description']
            else:
                data.pop('description', None)  # ['paths'][PATH][METHOD]['description']

                for p in data['parameters']:
                    p.pop(
                        'description', None
                    )  # ['paths'][PATH][METHOD]['parameters'][X]['description']

                for _, r in data['responses'].items():
                    r.pop(
                        'description', None
                    )  # ['paths'][PATH][METHOD]['responses'][STATUS_CODE]['description']

    for _, value in spec['definitions'].items():
        value.pop('title', None)  # ['definitions'][DEF]['title']
        value.pop('description', None)  # ['definitions'][DEF]['description']

        for _, prop in value['properties'].items():
            prop.pop('title', None)  # ['definitions'][DEF]['properties'][PROP]['title']
            prop.pop(
                'description', None
            )  # ['definitions'][DEF]['properties'][PROP]['description']

    return spec


class Command(SwaggerBaseCommand):
    def write_schema(self, schema, stream, format):
        if format != 'json':
            raise Exception('Should be json')

        codec = OpenAPICodecJson(validators=[], pretty=True)
        specs = codec.encode(schema).decode('utf-8')

        # Sort the dictionary or ever time it gets re-generated,
        # it's sorted differently and generates diffs on Git.
        json_schema = json.loads(specs)
        json_schema['definitions']['Job']['required'].sort()
        json_schema['definitions']['JobList']['required'].sort()

        stream.write(json.dumps(json_schema, sort_keys=True, indent=2))
