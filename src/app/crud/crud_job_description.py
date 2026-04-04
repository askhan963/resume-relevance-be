from fastcrud import FastCRUD

from ..models.job_description import JobDescription
from ..schemas.job_description import JobDescriptionCreateInternal, JobDescriptionRead

CRUDJobDescription = FastCRUD[
    JobDescription,
    JobDescriptionCreateInternal,
    JobDescriptionCreateInternal,
    JobDescriptionCreateInternal,
    JobDescriptionRead,
    JobDescriptionRead,
]
crud_job_description = CRUDJobDescription(JobDescription)
