import pytest
from datetime import datetime

from graphql import GraphQLEnumType, GraphQLEnumValue, GraphQLField, GraphQLNonNull, GraphQLString, GraphQLInt, \
    GraphQLArgument, GraphQLSchema, GraphQLObjectType

from gql.config import Config
from gql.query_parser import QueryParser
from gql.renderer_dataclasses import DataclassesRenderer


@pytest.fixture
def swapi_dataclass_renderer(swapi_schema):
    return DataclassesRenderer(swapi_schema, Config(schema='schemaurl', endpoint='schemaurl', documents=''))

@pytest.fixture
def github_dataclass_renderer(swapi_schema):
    return DataclassesRenderer(swapi_schema, Config(schema='schemaurl', endpoint='schemaurl', documents=''))


def test_renders_custom_headers(swapi_schema, swapi_parser, module_compiler):
    query = """
            query GetFilm {
              returnOfTheJedi: film(id: "1") {
                title
                director
              }
            }
        """

    custom_header = '# Works!'
    renderer = DataclassesRenderer(swapi_schema, Config(schema='schemaurl', endpoint='schemaurl', documents='', custom_header=custom_header))

    parsed = swapi_parser.parse(query)
    rendered = renderer.render(parsed)

    assert rendered
    assert custom_header in rendered


def test_simple_query(swapi_dataclass_renderer, swapi_parser, module_compiler):
    query = """
        query GetFilm {
          returnOfTheJedi: film(id: "1") {
            title
            director
          }
        }
    """

    parsed = swapi_parser.parse(query)
    rendered = swapi_dataclass_renderer.render(parsed)

    m = module_compiler(rendered)
    response = m.GetFilm.from_json("""
    {
        "data": {
            "returnOfTheJedi": {
                "title": "Return of the Jedi",
                "director": "George Lucas"
            }
        }
    }
    """)

    assert response

    data = response.data
    assert data.returnOfTheJedi.title == 'Return of the Jedi'
    assert data.returnOfTheJedi.director == 'George Lucas'


def test_simple_query_with_variables(swapi_dataclass_renderer, swapi_parser, module_compiler, mocker):
    query = """
        query GetFilm($id: ID!) {
          returnOfTheJedi: film(id: $id) {
            title
            director
          }
        }
    """

    parsed = swapi_parser.parse(query)
    rendered = swapi_dataclass_renderer.render(parsed)

    m = module_compiler(rendered)

    call_mock = mocker.patch.object(m.Client, 'call')
    call_mock.return_value = """
       {
           "data": {
               "returnOfTheJedi": {
                   "title": "Return of the Jedi",
                   "director": "George Lucas"
               }
           }
       }
    """

    result = m.GetFilm.execute('luke')
    assert result
    assert isinstance(result, m.GetFilm)

    data = result.data
    assert data.returnOfTheJedi.title == 'Return of the Jedi'
    assert data.returnOfTheJedi.director == 'George Lucas'


def test_simple_query_with_fragment(swapi_parser, swapi_dataclass_renderer, module_compiler):
    query = """
        query GetFilm {
          returnOfTheJedi: film(id: "1") {
            ...FilmFields
            openingCrawl

          }
        }

        fragment FilmFields on Film {
            title
            director
        }
    """

    parsed = swapi_parser.parse(query)
    rendered = swapi_dataclass_renderer.render(parsed)

    m = module_compiler(rendered)
    response = m.GetFilm.from_json("""
    {
        "data": {
            "returnOfTheJedi": {
                "title": "Return of the Jedi",
                "director": "George Lucas",
                "openingCrawl": "la la la"
            }
        }
    }
    """)

    assert response

    data = response.data
    assert data.returnOfTheJedi.title == 'Return of the Jedi'
    assert data.returnOfTheJedi.director == 'George Lucas'
    assert data.returnOfTheJedi.openingCrawl == 'la la la'


def test_simple_query_with_complex_fragment(swapi_parser, swapi_dataclass_renderer, module_compiler):
    query = """
        query GetPerson {
          luke: character(id: "luke") {
            ...CharacterFields
          }
        }

        fragment CharacterFields on Person {
            name

            home: homeworld {
                name
            }
        }
    """

    parsed = swapi_parser.parse(query)
    rendered = swapi_dataclass_renderer.render(parsed)

    m = module_compiler(rendered)
    response = m.GetPerson.from_json("""
    {
        "data": {
            "luke": {
                "name": "Luke Skywalker",
                "home": {
                    "name": "Arakis"
                }
            }
        }
    }
    """)

    assert response

    data = response.data
    assert data.luke.name == 'Luke Skywalker'
    assert data.luke.home.name == 'Arakis'


def test_simple_query_with_complex_fragments(swapi_parser, swapi_dataclass_renderer, module_compiler):
    query = """
        fragment PlanetFields on Planet {
          name
          population
          terrains
        }

        fragment CharacterFields on Person {
          name
          home: homeworld {
            ...PlanetFields
          }
        }

        query GetPerson {
          luke: character(id: "luke") {
            ...CharacterFields
          }
        }
    """

    parsed = swapi_parser.parse(query)
    rendered = swapi_dataclass_renderer.render(parsed)

    m = module_compiler(rendered)
    response = m.GetPerson.from_json("""
    {
        "data": {
            "luke": {
                "name": "Luke Skywalker",
                "home": {
                    "name": "Arakis",
                    "population": "1,000,000",
                    "terrains": ["Desert"]
                }
            }
        }
    }
    """)

    assert response

    data = response.data
    assert data.luke.name == 'Luke Skywalker'
    assert data.luke.home.name == 'Arakis'


def test_simple_query_with_complex_inline_fragment(swapi_parser, swapi_dataclass_renderer, module_compiler):
    query = """
        query GetPerson {
          luke: character(id: "luke") {
            ... on Person {
              name
              home: homeworld {
                name
              }
            }
          }
        }
    """

    parsed = swapi_parser.parse(query)
    rendered = swapi_dataclass_renderer.render(parsed)

    m = module_compiler(rendered)
    response = m.GetPerson.from_json("""
        {
            "data": {
                "luke": {
                    "name": "Luke Skywalker",
                    "home": {
                        "name": "Arakis"
                    }
                }
            }
        }
        """)

    assert response

    data = response.data
    assert data.luke.name == 'Luke Skywalker'
    assert data.luke.home.name == 'Arakis'


def test_simple_query_with_enums(github_parser, github_dataclass_renderer, module_compiler):
    query = """
        query MyIssues {
          viewer {
            issues(first: 5) {
              edges {
                node {
                  author { login }
                  authorAssociation
                }
              }
            }
          }
        }
    """
    parsed = github_parser.parse(query)
    rendered = github_dataclass_renderer.render(parsed)

    m = module_compiler(rendered)
    response = m.MyIssues.from_json("""
        {
            "data": {
                "viewer": {
                    "issues": {
                        "edges": [
                            {
                                "node": {
                                    "author": { "login": "whatever" },
                                    "authorAssociation": "FIRST_TIMER"
                                }
                            }
                        ]
                    }
                }
            }
        }
        """)

    assert response

    node = response.data.viewer.issues.edges[0].node
    assert node
    assert node.author.login == 'whatever'
    assert node.authorAssociation == m.CommentAuthorAssociation.FIRST_TIMER


def test_simple_query_with_enums_default_value(module_compiler):
    """
        enum LengthUnit {
          METER
          KM
        }

        type Starship {
          id: ID!
          name: String!
          length(unit: LengthUnit = METER): Float
        }

        type Query {
            ship(id: String!): Starship
        }
    """

    length_unit_enum = GraphQLEnumType(
        'LengthUnit',
        {
            'METER': GraphQLEnumValue('METER'),
            'KM': GraphQLEnumValue('KM'),
        },
        description='One of the films in the Star Wars Trilogy',
    )

    starship_type = GraphQLObjectType(
        'Starship',
        lambda: {
            'id': GraphQLField(GraphQLNonNull(GraphQLString), description='The id of the ship.'),
            'name': GraphQLField(GraphQLString, description='The name of the ship.'),
            'length': GraphQLField(
                GraphQLInt,
                args={
                    'unit': GraphQLArgument(
                        GraphQLNonNull(length_unit_enum), default_value='METER', description='id of the droid'
                    )
                }
            )
        }
    )

    query_type = GraphQLObjectType(
        'Query',
        lambda: {
            'ship': GraphQLField(
                starship_type,
                args={
                    'id': GraphQLArgument(GraphQLNonNull(GraphQLString), description='id of the ship')
                },
            )
        }
    )

    schema = GraphQLSchema(query_type, types=[length_unit_enum, starship_type])

    query = """
        query GetStarship {
            ship(id: "Enterprise") {
                id
                name
                length(unit: METER)
            }
        }
    """
    query_parser = QueryParser(schema)
    query_renderer = DataclassesRenderer(schema, Config(schema='schemaurl', endpoint='schemaurl', documents=''))
    parsed = query_parser.parse(query)
    rendered = query_renderer.render(parsed)

    m = module_compiler(rendered)
    response = m.GetStarship.from_json("""
        {
            "data": {
                "ship": {
                    "id": "Enterprise",
                    "name": "Enterprise",
                    "length": 100
                }
            }
        }
    """)

    assert response

    ship = response.data.ship
    assert ship
    assert ship.id == 'Enterprise'
    assert ship.name == 'Enterprise'
    assert ship.length == 100


def test_simple_query_with_datetime(swapi_dataclass_renderer, swapi_parser, module_compiler, mocker):
    query = """
        query GetFilm($id: ID!) {
          returnOfTheJedi: film(id: $id) {
            title
            director
            releaseDate
          }
        }
    """

    parsed = swapi_parser.parse(query)
    rendered = swapi_dataclass_renderer.render(parsed)

    m = module_compiler(rendered)

    now = datetime.now()

    call_mock = mocker.patch.object(m.Client, 'call')
    call_mock.return_value = """
       {
           "data": {
               "returnOfTheJedi": {
                   "title": "Return of the Jedi",
                   "director": "George Lucas",
                   "releaseDate": "%s"
               }
           }
       }
    """ % now.isoformat()

    result = m.GetFilm.execute('luke')
    assert result
    assert isinstance(result, m.GetFilm)

    data = result.data
    assert data.returnOfTheJedi.title == 'Return of the Jedi'
    assert data.returnOfTheJedi.director == 'George Lucas'
    assert data.returnOfTheJedi.releaseDate == now
