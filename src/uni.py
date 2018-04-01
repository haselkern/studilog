import datetime
from enum import Enum


class CourseState(Enum):
    PLANNED = 0
    PASSED = 1
    GRADED = 2
    FAILED = 3


class Semester(Enum):
    WINTER = 0
    SUMMER = 1

class Course:
    DEFAULT_GRADE = 1

    def __init__(self):
        self.title = ""
        self.type = ""
        self.credits = 6
        self.state = CourseState.PLANNED
        self.grade = None
        self.semester = Semester.WINTER
        self.year = datetime.datetime.now().year
        self.duration = 1

    def __repr__(self) -> str:
        return f"Course['{self.title}' {self.semester.name} {self.year}]"

    def __lt__(self, other):
        """Compares this course to another course, based on when it was.
        Summer 2018 < Winter 2018 < Summer 2020 < Winter 2030"""
        if self.year != other.year:
            return self.year < other.year
        else:
            return self.semester == Semester.SUMMER and other.semester == Semester.WINTER