import sys
from collections import OrderedDict

from PyQt5.QtCore import QCoreApplication, Qt, QRect
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget

import ui.mainwindow
import uni


class Rect(QRect):
    """Extends QRect to make it hashable, so that it can be used as a key in a dict."""
    def __hash__(self):
        return hash((self.x(), self.y(), self.width(), self.height()))


class CoursesWidget(QWidget):

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

        self.setAutoFillBackground(True)

        # Contains all the courses
        self.courses = []
        # Associates Rect with Course
        self.rectangles = {}

    def refresh(self):
        """Updates height and position of widget and contents and then repaints this widget."""
        self.update_rectangles()
        self.update_height()
        self.repaint()

    def update_height(self):
        """Update the height of this widget to match the containing courses."""
        max_y = max([r.y() + r.height() for r in self.rectangles] + [0])
        self.setMinimumHeight(max_y)

    def update_rectangles(self):
        """Update the dictionary that associates rectangles with courses."""
        self.rectangles.clear()

        # Store courses by year and semester
        courses_year_semester = {}
        for course in sorted(self.courses):
            key = (course.year, course.semester)
            if not key in courses_year_semester:
                courses_year_semester[key] = [course]
            else:
                courses_year_semester[key] += [course]

        # Layout rects
        pixels_per_credit = 20
        pixels_per_semester = 50
        y = 0
        for key in courses_year_semester:
            for course in courses_year_semester[key]:
                width = course.credits * pixels_per_credit / course.duration
                height = course.duration * pixels_per_semester
                # Always start at x=0 and then move rectangle to the right until it fits
                rect = Rect(0, y, width, height)

                # Check for intersections
                # This has to be repeated because once a rectangle is moved,
                # it might intersect with new rectangles
                moved = True
                while moved:
                    moved = False
                    for other_rect in self.rectangles:
                        if other_rect.intersects(rect):
                            rect.setX(other_rect.right() + 1)
                            rect.setWidth(width)
                            moved = True

                self.rectangles[rect] = course
                x = rect.right()
            y += pixels_per_semester

    def add_course(self, course):
        """Adds a new course to this widget."""
        self.courses.append(course)
        self.refresh()

    def mousePressEvent(self, event):
        for rectangle in self.rectangles:
            if rectangle.contains(event.x(), event.y()):
                self.callback.course_clicked(self.rectangles[rectangle])
                return

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        # Draw courses
        for rectangle in self.rectangles:
            qp.setBrush(QColor(255, 255, 255))
            qp.setPen(QColor(0, 0, 0))
            qp.drawRect(rectangle.x(), rectangle.y(), rectangle.width(), rectangle.height())
            course = self.rectangles[rectangle]
            qp.drawText(rectangle.x(), rectangle.y(), rectangle.width(), rectangle.height(), Qt.AlignCenter | Qt.TextWordWrap, course.title)

        qp.end()


class MainWindow(QMainWindow, ui.mainwindow.Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.selected_course = None
        self.courses_widget = CoursesWidget(self)
        self.courses_area.setWidget(self.courses_widget)

        self.course_settings_container.setVisible(False)

        # Menu actions
        self.action_quit.triggered.connect(self.quit)
        self.action_add_course.triggered.connect(self.add_course)

        # Listener for edited course
        self.course_title.textChanged.connect(self.course_edited)
        self.course_type.textChanged.connect(self.course_edited)
        self.course_credits.valueChanged.connect(self.course_edited)
        self.course_state.currentIndexChanged.connect(self.course_edited)
        self.course_grade.valueChanged.connect(self.course_edited)
        self.course_semester.currentIndexChanged.connect(self.course_edited)
        self.course_year.valueChanged.connect(self.course_edited)
        self.course_duration.valueChanged.connect(self.course_edited)

    def resizeEvent(self, *args, **kwargs):
        self.courses_widget.refresh()

    def course_edited(self):
        """Updates the selected course with values from the inputs."""
        if not self.selected_course is None:
            # Set values from inputs
            self.selected_course.title = self.course_title.text()
            self.selected_course.type = self.course_type.text()
            self.selected_course.credits = self.course_credits.value()
            self.selected_course.state = uni.CourseState(self.course_state.currentIndex())
            self.selected_course.grade = self.course_grade.value()
            self.selected_course.semester = uni.Semester(self.course_semester.currentIndex())
            self.selected_course.year = self.course_year.value()
            self.selected_course.duration = self.course_duration.value()

            # Enable/Disable widgets
            self.course_grade.setDisabled(self.selected_course.state != uni.CourseState.GRADED)

            # Refresh widget
            self.courses_widget.refresh()

    def course_clicked(self, course):
        """Sets the selected course to the input fields."""
        self.course_settings_container.setVisible(True)

        self.selected_course = None # Prevent connected function course_edited from changing course
        self.course_title.setText(course.title)
        self.course_type.setText(course.type)
        self.course_credits.setValue(course.credits)
        self.course_state.setCurrentIndex(course.state.value)
        self.course_grade.setValue(course.grade or uni.Course.DEFAULT_GRADE)
        self.course_semester.setCurrentIndex(course.semester.value)
        self.course_year.setValue(course.year)
        self.course_duration.setValue(course.duration)
        self.selected_course = course

        self.course_edited()
        self.courses_widget.refresh()

    def add_course(self):
        course = uni.Course()
        self.courses_widget.add_course(course)
        self.course_clicked(course)
        self.course_title.setFocus()

    def quit(self):
        QCoreApplication.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
