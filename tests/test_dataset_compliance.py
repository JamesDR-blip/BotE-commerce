from unittest.mock import Mock

import pytest

from application.datasets.dataset_service import DatasetService
from domain.compliance import CompliancePolicy
from domain.exceptions import ComplianceViolationError


def _service(*, policy: CompliancePolicy):
    datasets = Mock()
    projects = Mock()
    workspaces = Mock()
    authorization = Mock()
    quota_service = Mock()
    compliance = Mock()

    project = Mock()
    project.workspace_id = "workspace-1"
    projects.get_for_owner.return_value = project

    workspace = Mock()
    workspace.organization_id = "org-1"
    workspaces.get_for_owner.return_value = workspace

    def check(**kwargs):
        if policy.matches(
            resource=kwargs["resource"],
            action=kwargs["action"],
            context=kwargs["context"],
        ):
            raise ComplianceViolationError(
                organization_id="org-1",
                resource=kwargs["resource"],
                action=kwargs["action"],
                reason=policy.reason,
            )

    compliance.check.side_effect = check

    service = DatasetService(
        datasets=datasets,
        projects=projects,
        workspaces=workspaces,
        authorization=authorization,
        quota_service=quota_service,
        compliance_service=compliance,
    )
    return service, datasets, compliance


def test_create_dataset_is_blocked_by_matching_compliance_policy():
    service, datasets, compliance = _service(
        policy=CompliancePolicy(
            id="policy-1",
            organization_id="org-1",
            name="blocked-source",
            resource="dataset",
            action="write",
            condition={"source_type": "restricted"},
            reason="Restricted source requires governed handling.",
        )
    )

    with pytest.raises(ComplianceViolationError):
        service.create_dataset(
            dataset_id="dataset-1",
            project_id="project-1",
            name="Restricted",
            current_user=Mock(user_id="user-1"),
            source_type="restricted",
            metadata={},
        )

    datasets.create.assert_not_called()
    compliance.check.assert_called_once()


def test_create_dataset_allows_non_matching_compliance_policy():
    service, datasets, compliance = _service(
        policy=CompliancePolicy(
            id="policy-1",
            organization_id="org-1",
            name="blocked-source",
            resource="dataset",
            action="write",
            condition={"source_type": "restricted"},
            reason="Restricted source requires governed handling.",
        )
    )

    datasets.create.return_value = "created"

    result = service.create_dataset(
        dataset_id="dataset-1",
        project_id="project-1",
        name="Public",
        current_user=Mock(user_id="user-1"),
        source_type="public",
        metadata={},
    )

    assert result == "created"
    datasets.create.assert_called_once()
    compliance.check.assert_called_once()
