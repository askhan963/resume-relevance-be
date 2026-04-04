from fastcrud import FastCRUD

from ..models.resume import Resume
from ..schemas.resume import ResumeCreateInternal, ResumeRead

CRUDResume = FastCRUD[Resume, ResumeCreateInternal, ResumeCreateInternal, ResumeCreateInternal, ResumeRead, ResumeRead]
crud_resume = CRUDResume(Resume)
