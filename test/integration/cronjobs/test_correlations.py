import textwrap

from howler.cronjobs.correlations import (
    create_correlated_bundle,
    create_executor,
)
from howler.odm.models.analytic import Analytic
from howler.odm.models.hit import Hit
from howler.odm.random_data import create_hits
from howler.odm.randomizer import random_model_obj


def test_correlated_bundle(datastore_connection):
    correlation: Analytic = random_model_obj(Analytic)
    correlation.correlation = "howler.id:*"
    correlation.correlation_type = "lucene"
    correlation.correlation_crontab = "0 0 * * *"

    child_hits = [random_model_obj(Hit), random_model_obj(Hit)]

    correlated_bundle = create_correlated_bundle(
        correlation, correlation.correlation, child_hits
    )

    datastore_connection.hit.commit()

    correlated_bundle_2 = create_correlated_bundle(
        correlation, correlation.correlation, child_hits
    )

    correlated_bundle_3 = create_correlated_bundle(
        correlation,
        correlation.correlation,
        [random_model_obj(Hit), random_model_obj(Hit)],
    )

    assert correlated_bundle.howler.analytic == correlation.name
    assert correlated_bundle.howler.id == correlated_bundle_2.howler.id
    assert correlated_bundle_3.howler.id != correlated_bundle_2.howler.id


def test_executor(datastore_connection):
    create_hits(datastore_connection, hit_count=10)

    datastore_connection.hit.commit()

    lucene_correlation: Analytic = random_model_obj(Analytic)
    lucene_correlation.correlation = "howler.id:*"
    lucene_correlation.correlation_type = "lucene"
    lucene_correlation.correlation_crontab = "0 0 * * *"

    lucene_executor = create_executor(lucene_correlation)

    eql_correlation: Analytic = random_model_obj(Analytic)
    eql_correlation.correlation = """
    sequence with maxspan=3000h
        [any where howler.score > 0]
        [any where howler.score > 100]
    """
    eql_correlation.correlation_type = "eql"
    eql_correlation.correlation_crontab = "0 0 * * *"

    eql_executor = create_executor(eql_correlation)

    sigma_correlation: Analytic = random_model_obj(Analytic)
    sigma_correlation.correlation = textwrap.dedent(
        """
        title: Example Howler Sigma Rule
        id: 811ac553-c775-4dea-a65b-d0d2e6d6bf82
        status: test
        description: A basic example of using sigma rule notation to query howler
        references:
            - https://github.com/SigmaHQ/sigma
        author: You
        date: 2024/01/25
        modified: 2024/01/25
        tags:
            - attack.command_and_control
        logsource:
            category: nbs
        detection:
            selection1:
                howler.status:
                - resolved
                - on-hold
            selection2:
                howler.status:
                - open
                - in-progress
            condition: 1 of selection*
        falsepositives:
            - Unknown
        level: informational
        """
    )
    sigma_correlation.correlation_type = "sigma"
    sigma_correlation.correlation_crontab = "0 0 * * *"

    sigma_executor = create_executor(sigma_correlation)

    not_a_correlation: Analytic = random_model_obj(Analytic)
    not_a_correlation.correlation = None
    not_a_correlation.correlation_type = None
    not_a_correlation.correlation_crontab = None

    # No in-depth testing of results, just making sure basic executors run without errors
    lucene_executor()
    eql_executor()
    sigma_executor()
    create_executor(not_a_correlation)()
