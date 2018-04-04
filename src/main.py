import os
import pathlib
import sys

import jsonpickle
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QColor, QIcon
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QMessageBox

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
        self.update_size()
        self.repaint()

    def update_size(self):
        """Update the height of this widget to match the containing courses."""
        max_y = max([r.y() + r.height() for r in self.rectangles] + [0])
        max_x = max([r.x() + r.width() for r in self.rectangles] + [0])
        self.setMinimumHeight(max_y)
        self.setMinimumWidth(max_x)

    def update_rectangles(self):
        """Update the dictionary that associates rectangles with courses."""
        self.rectangles.clear()

        # Store courses by date index
        courses_by_date_index = {}
        for course in sorted(self.courses):
            key = course.date_index()
            if not key in courses_by_date_index:
                courses_by_date_index[key] = [course]
            else:
                courses_by_date_index[key] += [course]

        # Layout rects
        pixels_per_credit = 25
        pixels_per_semester = 50
        lowest_date_index = min([c.date_index() for c in self.courses], default=0) # is used to calculate y
        for key in courses_by_date_index:
            for course in courses_by_date_index[key]:
                width = course.credits * pixels_per_credit / course.duration
                height = course.duration * pixels_per_semester
                # Always start at x=0 and then move rectangle to the right until it fits
                y = (course.date_index() - lowest_date_index) * pixels_per_semester
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

    def add_course(self, course):
        """Adds a new course to this widget."""
        self.courses.append(course)
        self.refresh()

    def delete_course(self, course):
        if not course is None:
            self.courses.remove(course)
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

    SAVE_FILE = "courses.json"
    APP_NAME = "StudiLog"

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.selected_course = None
        self.courses_widget = CoursesWidget(self)
        self.courses_widget.courses = self.load()
        self.courses_area.setWidget(self.courses_widget)

        self.course_settings_container.setVisible(False)

        # Menu actions
        self.action_quit.triggered.connect(self.quit)
        self.action_add_course.triggered.connect(self.add_course)
        self.action_delete_course.triggered.connect(self.delete_course)
        self.action_save.triggered.connect(self.save)

        # Listener for edited course
        self.course_title.textChanged.connect(self.course_edited)
        self.course_type.textChanged.connect(self.course_edited)
        self.course_credits.valueChanged.connect(self.course_edited)
        self.course_state.currentIndexChanged.connect(self.course_edited)
        self.course_grade.valueChanged.connect(self.course_edited)
        self.course_semester.currentIndexChanged.connect(self.course_edited)
        self.course_year.valueChanged.connect(self.course_edited)
        self.course_duration.valueChanged.connect(self.course_edited)

        # Set icon
        icon = QIcon("res/icon.png")
        self.setWindowIcon(icon)

        # Setup title
        self.set_dirty(False)

    def resizeEvent(self, *args, **kwargs):
        self.courses_widget.refresh()

    def closeEvent(self, event):
        """Ask before quitting, when there are unsaved changes"""
        if self.dirty:
            box = QMessageBox(self)
            box.setWindowTitle(MainWindow.APP_NAME)
            box.setText("Es sind ungespeicherte Änderungen vorhanden. Wirklich beenden?")
            button_yes = box.addButton("Ja", QMessageBox.YesRole)
            button_no = box.addButton("Nein", QMessageBox.NoRole)
            box.exec()
            if box.clickedButton() == button_yes:
                event.accept()
            else:
                event.ignore()

    def set_dirty(self, dirty):
        self.dirty = dirty
        """Called from courses_widgets, to signal that unsaved changes occured."""
        if dirty:
            self.setWindowTitle(MainWindow.APP_NAME + " - nicht gespeichert")
        else:
            self.setWindowTitle(MainWindow.APP_NAME)

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

            self.courses_widget.refresh()
            self.set_dirty(True)
            self.update_details()

    def update_details(self):
        # Enable/Disable widgets
        self.course_grade.setDisabled(self.selected_course.state != uni.CourseState.GRADED)

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

        self.courses_widget.refresh()
        self.course_title.setFocus()
        self.update_details()

    def add_course(self):
        course = uni.Course()
        self.courses_widget.add_course(course)
        self.course_clicked(course)
        self.course_title.setFocus()
        self.set_dirty(True)

    def delete_course(self):
        self.course_settings_container.setVisible(False)
        self.courses_widget.delete_course(self.selected_course)
        self.selected_course = None
        self.set_dirty(True)

    @staticmethod
    def get_save_folder():
        data_dir = str(pathlib.Path.home()) + "/.haselkern/studilog/"
        try:
            os.makedirs(data_dir)
        except:
            # Folder already exists, that's fine
            pass
        return data_dir

    def save(self):
        json_courses = jsonpickle.encode(self.courses_widget.courses)
        with open(MainWindow.get_save_folder() + MainWindow.SAVE_FILE, "w") as f:
            f.write(json_courses)
        self.set_dirty(False)

    @staticmethod
    def load():
        try:
            with open(MainWindow.get_save_folder() + MainWindow.SAVE_FILE) as f:
                return jsonpickle.decode(f.read())
        except:
            return []

    def quit(self):
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
