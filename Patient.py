from tabulate import tabulate
from main import User, MenuHelper
from encryption import EncryptionHelper
from parser_help import Parser
from database import SQLQuery
# import sys
import time
import datetime
import random
from exceptions import DBRecordError

print_clean = Parser.print_clean
delta = datetime.timedelta

class Patient(User):
    """
    patient Class with navigation options and various functionalities.
    """

    def main_menu(self) -> None:
        """
        Main Menu for Patient-type users.
        """
        while True:
            print("You're currently viewing main menu options for Patient {}.".format(self.username))
            option_selection = Parser.selection_parser(
                options={"B": "book appointments", "I":"view /check in unattended appointment", "C": "cancel appiontment", "R": "review/rate appointments",
                         "--logout": "Logout"})
            if option_selection == "--logout":
                # Quitting is required for logout to ensure all personal data is cleared from session
                print_clean("Logging you out...")
                Parser.user_quit()
            elif option_selection == "B":
                self.book_appointment_start()
            elif option_selection == "I":
                self.check_in_appointment()
            elif option_selection == "C":
                self.cancel_appointment()
            elif option_selection == "R":
                r_selection = Parser.selection_parser(options={"A": "review", "B": "rate", "--back": "back"})
                if r_selection == "--back":
                    print_clean("back...")
                elif r_selection == "A":
                    self.review_appointment()
                elif r_selection == "B":
                    self.rate_appointment()



    def book_appointment_start(self):
        """
        choose a date -- choose a GP
        --choose time
        --give random number as bookingNo
        --move from available_time
        --insert in visit

        """
        stage = 0
        while True:
            while stage == 0:

                result = SQLQuery(
                    "SELECT  StaffID, Timeslot FROM available_time "
                    "WHERE Timeslot >= ? AND Timeslot <= ? "
                    "ORDER BY Timeslot"
                    #"ORDER BY   DATE_FORMAT(Timeslot,'%Y-%m-%d %H:%i:%s')"
                    #CONVERT(varchar(100), Timeslot, 120)
                ).executeFetchAll(parameters=(datetime.datetime.now().date(), datetime.datetime.now().date() + delta(days=14)))
                    # "ORDER BY   DATE_FORMAT(Timeslot,'%Y-%m-%d %H:%i:%s')"
                    # CONVERT(varchar(100), Timeslot, 120)

                if len(result) == 0:
                    print(f"there is no booking  yet.")
                    stage = 0
                    input("Press Enter to continue.")
                else:
                    result_table = []
                    # # result_table_raw = []
                    # dateTime = []
                    # # result_table_raw = []
                    for i in range(len(result)):
                    #     # gp_table.append(str(gp_result[i]))
                        result_table.append([i+1, str(result[i][0]), str(result[i][1])])
                    #     # print(result[i][1])
                    #     dateTime = datetime.datetime.strptime(str(result[i][1]), '%Y-%m-%d %H:%M:%S')
                    #     # print(dateTime.time())
                    #     result_table.append([result[i][0], dateTime.date(), dateTime.time()])
                    #
                    # bubbleSort(result_table, 1)
                    # bubbleSort(result_table, 2)
                    #
                    # result_sorted = []
                    # for i in range(len(result_table)):
                    #     timeslot = str(result_table[i][1]) + ' ' + str(result_table[i][2])
                    #     result_sorted.append([i + 1, result_table[i][0], timeslot])
                    #     # print(timeslot)

                    print(tabulate(result_table, headers=["Pointer", "GP", "timeslot"]))

                stage = 1
            while stage == 1:
                print(f"How would you like to choose")
                booking_selection = Parser.selection_parser(options={"G": "select by GP number", "D": "select by date", "--back": "back"})
                if booking_selection == "D":
                    self.book_appointment_date()
                elif booking_selection == "G":
                    self.book_appointment_GP()
                elif booking_selection == "--back":
                    return

    def book_appointment_date(self):
        stage = 0
        while True:
            while stage == 0:
                booking_selection = Parser.selection_parser(options={"E": "select earliest one", "D": "select by date", "--back": "back"})
                if booking_selection == "E":
                    stage = 1
                elif booking_selection == "D":
                    stage = 2
                elif booking_selection == "--back":
                    return
            while stage == 1:
                result = SQLQuery(
                    "SELECT  StaffID, Timeslot FROM available_time "
                    "WHERE Timeslot >= ? AND Timeslot <= ? "
                    "ORDER BY Timeslot"
                    "LIMIT 1"
                    # "ORDER BY   DATE_FORMAT(Timeslot,'%Y-%m-%d %H:%i:%s')"
                    # CONVERT(varchar(100), Timeslot, 120)
                ).executeFetchAll(parameters=(selected_date, selected_date + delta(days=1)))

                selected_row_raw = result[0]
                print(f"You are viewing early available for: {selected_date}")
                # print(selected_row_raw)
                print(tabulate([selected_row_raw], headers=["GP", "timeslot"]))
                stage = 3
            while stage == 2:
                selected_date = Parser.date_parser(question=f"Managing for Patient {self.username}.\n"
                                                            "Select a Date:\n")
                if selected_date == "--back":
                    print_clean()
                    return

                result = SQLQuery(
                    "SELECT  StaffID, Timeslot FROM available_time "
                    "WHERE Timeslot >= ? AND Timeslot <= ? "
                    "ORDER BY Timeslot"
                    # "ORDER BY   DATE_FORMAT(Timeslot,'%Y-%m-%d %H:%i:%s')"
                    # CONVERT(varchar(100), Timeslot, 120)
                ).executeFetchAll(parameters=(selected_date, selected_date + delta(days=1)))

                if len(result) == 0:
                    print(f"there is no booking for this day yet.")
                    stage = 0
                    input("Press Enter to continue.")
                else:
                    result_table = []

                    for i in range(len(result)):
                        result_table.append([i + 1, result[i][0],result[i][1]])

                    print(f"You are viewing all available appointment for: {selected_date}")
                    print(tabulate(result_table, headers=["Pointer", "GP", "timeslot"]))

                    selected_appointment = Parser.pick_pointer_parser("Select an appointment by the Pointer.",
                                                                      (1, len(result_table)))

                    if selected_appointment == '--back':
                        return False

                    #selected_row = result_table[selected_appointment - 1]
                    selected_row_raw = result_table[selected_appointment - 1]
                    stage = 3

            while stage == 3:
                self.book_appointment_end(selected_row_raw)


    #
    def book_appointment_GP(self):
        stage = 0
        while True:
            while stage == 0:
                gp_result = SQLQuery(
                    "SELECT users.lastName, GP.Introduction, GP.ClinicAddress, GP.ClinicPostcode, GP.Gender, "
                    "GP.Rating, users.ID FROM GP INNER JOIN users ON "
                    "GP.ID = users.ID WHERE users.ID IN ( SELECT DISTINCT StaffID FROM available_time "
                    "WHERE Timeslot >= ? AND Timeslot <= ? )"
                ).executeFetchAll(
                    parameters=(datetime.datetime.now().date(), datetime.datetime.now().date() + delta(days=14)))

                gp_table = []

                for i in range(len(gp_result)):
                    # gp_table.append(str(gp_result[i]))
                    #print(EncryptionHelper().decryptMessage(gp_result[i][1]))
                    gp_table.append([i + 1, EncryptionHelper().decryptMessage(gp_result[i][0]),
                                     str(gp_result[i][1]),
                                     EncryptionHelper().decryptMessage(gp_result[i][2]),
                                     EncryptionHelper().decryptMessage(gp_result[i][3]),
                                     str(gp_result[i][4]),
                                     str(gp_result[i][5]),
                                     str(gp_result[i][6])])

                if len(gp_table) == 0:
                    print(f"there is no GP yet.")
                    stage = 0
                    input("Press Enter to continue.")
                else:
                    print(f"You are viewing all available GP ")

                    print(tabulate(gp_table,
                                   headers=["Pointer", "lastname", "Introduction", "ClinicAddress", "ClinicPostcode",
                                            "Gender", "Rating"]))

                    selected_gp_pointer = Parser.pick_pointer_parser("Select GP by the Pointer.",
                                                                     (1, len(gp_table)))
                    if selected_gp_pointer == '--back':
                        return False


                    selected_gp_row = gp_table[selected_gp_pointer - 1]
                    print(selected_gp_row[7])
                    # print(selected_gp)
                    appointment_result = SQLQuery(
                        "SELECT StaffID, Timeslot FROM available_time "
                        "WHERE StaffID = ? AND Timeslot >= ? AND Timeslot <= ?",
                    ).executeFetchAll(parameters=(selected_gp_row[7], datetime.datetime.now().date(), datetime.datetime.now().date() + delta(days=14)))

                    appointment_table = []
                    appointment_table_raw = []
                    for i in range(len(appointment_result)):
                        appointment_table.append([i + 1, str(appointment_result[i][0]), str(appointment_result[i][1])])
                        appointment_table_raw.append([i + 1, appointment_result[i][0], appointment_result[i][1]])

                    print(f"You are viewing your schedule for: {selected_gp_pointer}")

                    if len(appointment_table) == 0:
                        print(f"there is no booking for this day yet.")
                        input("Press Enter to continue...")
                        stage = 0
                    else:
                        print(tabulate(appointment_table, headers=["Pointer", "GP", "Timeslot"]))

                    selected_appointment = Parser.pick_pointer_parser("Select an appointment by the Pointer.",
                                                                      (1, len(appointment_table)))

                    if selected_appointment == '--back':
                        return False

                    # selected_row = result_table[selected_appointment - 1]
                    selected_row_raw = appointment_table[selected_appointment - 1]
                    stage = 1


                    # selected_gp_pointer = Parser.pick_pointer_parser("Select GP by the Pointer.",
                    #                                                  (1, len(gp_table)))
                    # if len(appointment_table) == 0:
                    #     print(f"there is no booking for this day yet.")
                    #     input("Press Enter to continue...")
                    #     stage = 0
                    # else:
                    #     print(tabulate(appointment_table, headers=["Pointer", "GP", "Timeslot"]))

            while stage == 1:
                self.book_appointment_end(selected_row_raw)

    #
    # def book_appointment_desceiption(self, result_sorted):
    def book_appointment_end(self,selected_row_raw):
        stage = 0
        while True:
            while stage == 0:
                print("This is time slot will be booked by you:")
                # print(selected_row_raw)
                print(tabulate([selected_row_raw], headers=["Pointer", "GP", "Timeslot"]))

                confirm = Parser.selection_parser(options={"Y": "Confirm", "N": "Go back and select again"})
                # Confirm if user wants to delete slots
                if confirm == "Y":
                    try:
                        repeat_booking_num = 1
                        while (repeat_booking_num):
                            booking_no = random.randint(100000, 999999)

                            visit_same_booking_no = SQLQuery(
                                "SELECT bookingNo FROM visit WHERE bookingNo = ? ").executeFetchAll(parameters=(booking_no,))
                            if len(visit_same_booking_no) == 0:

                                break
                            else:
                                repeat_booking_num = 1

                        print(selected_row_raw[1], selected_row_raw[2])

                        visit_same_booking_num = SQLQuery(
                            "SELECT StaffID, Timeslot FROM visit WHERE StaffID = ? AND Timeslot = ? ").executeFetchAll(
                            parameters=(selected_row_raw[1], selected_row_raw[2]))
                        if len(visit_same_booking_no) != 0:
                            # repeat_timeslot_num = 0
                            print("This time slot has been booked")
                            return False
                        else:

                            SQLQuery("INSERT INTO visit VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                                     ).executeCommit(
                                (booking_no, self.ID, selected_row_raw[1], selected_row_raw[2], "", "F", "F", "", "", "0"))
                            SQLQuery("DELETE FROM available_time WHERE StaffID = ? AND Timeslot = ?"
                                     ).executeCommit((selected_row_raw[1], selected_row_raw[2]))

                            print("booked successfully.")

                            visit_result = SQLQuery("SELECT bookingNo, NHSNo, StaffID, Timeslot FROM visit "
                                                    "WHERE bookingNo = ? "
                                                    ).executeFetchAll(parameters=(booking_no,))

                            print(tabulate(visit_result, headers=["bookingNo", "NHSNo", "GP", "Timeslot"]))

                            stage = 1

                            input("Press Enter to continue...")

                    except DBRecordError:
                        print("Error encountered")
                        input("Press Enter to continue...")
                if confirm == "N":
                    print("book cancelled.")
                    input("Press Enter to continue...")
                    return self.main_menu()

                while stage == 1:
                    print_clean()

                    info_input = Parser.string_parser("Please write description about your illness before the appointment: ")
                    SQLQuery(" UPDATE Visit SET PatientInfo = ? WHERE BookingNo = ? "
                             ).executeCommit((info_input, booking_no))
                    Parser.print_clean("Your description have been recorded successfully!")
                    Parser.string_parser("Press Enter to continue...")
                    return self.main_menu()



    def check_in_appointment(self):
        """
        show all booking
        if time later, allow to check in
        change attend to T
        """
        stage = 0
        while True:
            while stage == 0:
                print("This is time slot booked by you:")
                patient_appointment_result = SQLQuery(
                    "SELECT bookingNo, NHSNo, StaffID, Timeslot, Confirmed FROM visit "
                    "WHERE NHSNo = ? AND Attended = ? ",
                ).executeFetchAll(parameters=(self.ID,"F"))

                patient_confirmed_appointment_table = []
                patient_unconfirmed_appointment_table = []

                j=0
                for i in range(len(patient_appointment_result)):

                    if patient_appointment_result[i][4] == "T":
                        patient_confirmed_appointment_table.append([i + 1, str(patient_appointment_result[i][0]),
                                                             str(patient_appointment_result[i][1]),
                                                             str(patient_appointment_result[i][2]),
                                                             str(patient_appointment_result[i][3]),
                                                             str(patient_appointment_result[i][4])])

                    elif patient_appointment_result[i][4] == "F":
                        patient_unconfirmed_appointment_table.append([j + 1, str(patient_appointment_result[i][0]),
                                                                    str(patient_appointment_result[i][1]),
                                                                    str(patient_appointment_result[i][2]),
                                                                    str(patient_appointment_result[i][3]),
                                                                    str(patient_appointment_result[i][4])])
                        j = j + 1
                    else:
                        print("error")

                print(f"You are viewing all your unattended appointment: ")

                if len(patient_confirmed_appointment_table) == 0 and len(patient_unconfirmed_appointment_table) == 0:
                    print(f"You don't have any unattended appointment")
                    input("Press Enter to continue...")
                    stage = 0

                if not len(patient_confirmed_appointment_table) == 0 :
                    print(f"These are appointments already confirmed by GP")
                    print(tabulate(patient_confirmed_appointment_table, headers=["pointer","bookingNo", "NHSNo", "staffID", "timeslot", "confirmed"]))

                if not len(patient_unconfirmed_appointment_table) == 0 :
                    print(f"These appointment have not been confirmed by GP, please wait or change your appointment ")
                    print(tabulate(patient_unconfirmed_appointment_table, headers=["pointer","bookingNo", "NHSNo", "staffID", "timeslot", "confirmed"]))


                option_selection = Parser.selection_parser(
                        options={"I":"check in confirmed appointment","C": "change appointment","--back": "back"})
                if option_selection == "--back":
                     return
                elif option_selection == "C":
                     return
                elif option_selection == "I":
                    stage = 1

            while stage == 1:
                
                
                
                print(f"These are your unattended appointments ")
                print(tabulate(patient_confirmed_appointment_table,
                               headers=["pointer", "bookingNo", "NHSNo", "staffID", "timeslot", "confirmed"]))
                print("please check in after your attending")

                selected_appointment = Parser.list_number_parser("Select an appointment by the Pointer.",
                                                                      (1, len(patient_confirmed_appointment_table)))

                if selected_appointment == '--back':
                    return

                appointment_to_check_in = []

                for row in patient_confirmed_appointment_table:
                    if row[0] in selected_appointment:
                        appointment_date = datetime.datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S')
                        if appointment_date <= datetime.datetime.now() :
                            appointment_to_check_in.append([row[0],row[1],row[2],row[3],row[4]])
                        else:
                            print("Sorry, you can not check in before your appointment")
                            print(f"check in for: {row[4]} failed")

                if len(appointment_to_check_in) == 0:
                    print(f"There is no appointment can be checked in")
                    input("Press Enter to continue...")
                    stage = 1
                else:

                    print(f"These are your appointments selected to check in")
                    print("\n")
                    print(tabulate(appointment_to_check_in,
                                   headers=["pointer", "bookingNo", "NHSNo", "staffID", "timeslot", "confirmed"]))
                    print("\n")

                    confirm = Parser.selection_parser(options={"Y": "check in", "N": "Go back"})
                    if confirm == "Y":
                        try:
                            for appointment in appointment_to_check_in:
                                SQLQuery(" UPDATE Visit SET Attended = ? WHERE BookingNo = ? "
                                         ).executeCommit(("T", appointment[1]))

                            print("check in successfully.")
                            input("Press Enter to continue...")
                            return True
                        # temporary exception
                        except DBRecordError:
                            print("Error encountered")
                            slots_to_remove = []
                            input("Press Enter to continue...")
                    if confirm == "N":
                        print("Removal cancelled.")
                        slots_to_remove = []
                        input("Press Enter to continue...")

    def cancel_appointment(self):
        """
        bookings can be cancelled five days in advance
        move from visit
        insert in available time
        """
        stage = 0
        while True:
            while stage == 0:
                query_string = "SELECT BookingNo, NHSNo, StaffID, Timeslot, PatientInfo" \
                               "FROM visit  WHERE NHSNo = ? AND Timeslot >= ? "
                all_valid_cancel = SQLQuery(query_string)
                all_valid_cancel_result = all_valid_cancel.executeFetchAll(
                    parameters=(self.ID,datetime.datetime.now() + datetime.timedelta(days=5)))
                cancel_table = []
                cancel_table_raw = []
                cancel_pointer = []

                for i in range(len(all_valid_cancel_result)):
                    cancel_table.append([i + 1, str(all_valid_cancel_result[i][0]),str(all_valid_cancel_result[i][1]),
                                         str(all_valid_cancel_result[i][2]),str(all_valid_cancel_result[i][3]),
                                         str(all_valid_cancel_result[i][4])])
                    cancel_table_raw.append([i + 1, all_valid_cancel_result[i][0],all_valid_cancel_result[i][1],
                                             all_valid_cancel_result[i][2],all_valid_cancel_result[i][3],
                                             all_valid_cancel_result[i][4]])
                    cancel_pointer.append(i + 1)
                print(f"You are viewing all the appointments can be cancelled.")
                if len(cancel_table) == 0:
                    print(f"No Appointments can be cancelled.\n")
                    return
                else:
                    stage = 1

            while stage == 1:
                print(tabulate(cancel_table, headers = ["Pointer","BookingNo", "NHSNo",
                                                        "StaffID", "Timeslot","PatientInfo"]))
                selected_cancel_appointment = Parser.pick_pointer_parser("Select an appointment "
                                                                       "to cancel by the Pointer.",
                                                                       (1,len(cancel_table)))

                selected_row = cancel_table[selected_cancel_appointment - 1]
                selected_row_raw = cancel_table_raw[selected_cancel_appointment - 1]

                print("This is appointment you want to cancel:")
                print(tabulate([selected_row],headers = ["Pointer","BookingNo", "NHSNo",
                                                        "StaffID", "Timeslot","PatientInfo"]))

                confirmation = Parser.selection_parser(options= {"Y":"Confirm","N": "Go back and select again"})
                if confirmation == "Y":
                    SQLQuery("DELETE FROM visit WHERE BookingNo = ? "
                             ).executeCommit(parameters = (selected_row_raw[1]))
                    SQLQuery("INSERT INTO available_time VALUES (?,?)"
                             ).executeCommit(parameters = (selected_row_raw[3],selected_row_raw[4]))
                    print("Appointment is cancelled successfully.")

                    visit_result = SQLQuery("SELECT bookingNo, NHSNo, StaffID, Timeslot, PatientInfo FROM visit "
                                            "WHERE NHSNo = ? AND Timeslot >= ? "
                                            ).executeFetchAll(parameters = (self.ID,datetime.datetime.now() + datetime.timedelta(days=5)))

                    print(tabulate(visit_result, headers=["bookingNo", "NHSNo", "GP", "Timeslot","PatientInfo"]))

                else:
                    Parser.print_clean()
                    return

    def review_appointment(self):

        while True:
            record_viewer = Parser.selection_parser(
                options={"A": "Review Appointments", "B": "Review Prescriptions",
                         "--back": "back"})

            if record_viewer == "--back":
                Parser.print_clean("\n")
                return
            elif record_viewer == "A":
                query_string = "SELECT visit.BookingNo, visit.NHSNo, users.firstName, users.lastName, " \
                               "visit.Timeslot, visit.PatientInfo, visit.Confirmed, visit.Attended,visit.Rating " \
                               "FROM visit INNER JOIN users ON " \
                               "visit.NHSNo = users.ID WHERE visit.NHSNo = ? "
                headers = ("BookingNo", "NHSNo", "Firstname", "Lastname", "Timeslot",
                           "PatientInfo", "Confirmed", "Attended", "Rating")

            else:
                query_string = "SELECT prescription.BookingNo, users.ID, users.firstName, users.lastName, " \
                               "visit.PatientInfo, visit.Diagnosis, visit.Notes, prescription.drugName, " \
                               "prescription.quantity, prescription.Instructions " \
                               "FROM (visit INNER JOIN users ON visit.NHSNo = users.ID) " \
                               "INNER JOIN prescription ON " \
                               "visit.BookingNo = prescription.BookingNo WHERE visit.NHSNo = ? "

                headers = ("BookingNo", "NHSNo", "Firstname", "Lastname", "PatientInfo", "Diagnosis",
                           "DrugName", "Quantity", "Instructions", "Notes")

            query = SQLQuery(query_string)
            all_data = query.executeFetchAll(decrypter=EncryptionHelper(), parameters=(self.ID,))

            if len(list(all_data)) == 0:
                Parser.print_clean("No records Available.\n")
            else:
                print(tabulate(all_data, headers))

    def rate_appointment(self):
        """
        show appointment rate
        choose one appointment tp rate
        confirm and update in database


        （set default as 5）

        """
        while True:
            stage = 0
            while True:
                while stage == 0:
                    patient_result = SQLQuery(
                        "SELECT bookingNo, StaffID, Timeslot, Rating FROM visit "
                        "WHERE NHSNo = ? AND Attended = ? ",
                    ).executeFetchAll(parameters=(self.ID, "T"))

                    patient_attended_appointment_table = []
                    #patient_unconfirmed_appointment_table_raw = []
                    if len(patient_result) == 0 :
                        print(f"You don't have any attended appointment")
                        input("Press Enter to back...")
                        return
                    else:
                        for i in range(len(patient_result)):
                            patient_attended_appointment_table.append([i + 1, str(patient_result[i][0]),
                                                                            str(patient_result[i][1]),
                                                                            str(patient_result[i][2]),
                                                                            str(patient_result[i][3])])
                        # print("This is appointments attended by you:")
                        # print(tabulate(patient_attended_appointment_table,headers=["pointer", "bookingNo", "staffID", "timeslot"]))
                        #stage = 1

                #while stage == 1:

                    print("This is appointments attended by you:")
                    print(tabulate(patient_attended_appointment_table,
                                   headers=["pointer", "bookingNo", "staffID", "timeslot", "rating"]))

                    print("We think highly of your feelings, please give a rate to your GP")

                    selected_rate_appointment = Parser.pick_pointer_parser("Select an appointment "
                                                                             "to rate by the Pointer.",
                                                                             (1, len(patient_attended_appointment_table)))
                    if selected_rate_appointment == "--back":
                        Parser.print_clean("\n")
                        return

                    selected_row = patient_attended_appointment_table[selected_rate_appointment - 1]

                    print("This is the appointment you want to rate:")
                    print(tabulate([selected_row], headers=["pointer", "bookingNo", "staffID", "timeslot", "rating"]))

                    rate_selection = Parser.selection_parser(options={"Y": "Rate", "N": "Go back"})

                    if rate_selection == "N":
                            return
                    elif rate_selection == "Y":
                        try:
                            selected_rate = Parser.pick_pointer_parser("Select form 0 - 5 ", (0, 5))

                            SQLQuery(" UPDATE Visit SET Rating = ? WHERE BookingNo = ? "
                                     ).executeCommit((selected_rate, selected_row[1]))

                            #print(selected_row[2])

                            gp_rate_result = SQLQuery("SELECT Rating FROM visit WHERE StaffID = ? "
                                     ).executeFetchAll(parameters=(selected_row[2],))
                            gp_rate_num = 0

                            #print(gp_rate_result)
                            if not gp_rate_result == 0:

                                for i in range(len(gp_rate_result)):
                                    #print(gp_rate_result[i][0])
                                    gp_rate_num = gp_rate_num + gp_rate_result[i][0]

                                gp_rate_average = round((gp_rate_num/len(gp_rate_result)),2)
                                #print(gp_rate_average)

                                SQLQuery(" UPDATE GP SET Rating = ? WHERE ID = ? "
                                         ).executeCommit((gp_rate_average, selected_row[2]))
                                print("Your rate have been recorded successfully!")

                            else:
                                gp_rate_num = selected_rate
                                # print(gp_rate_num )
                                SQLQuery(" UPDATE gp SET Rating = ? WHERE ID = ? "
                                         ).executeCommit((gp_rate_num , selected_row[2]))
                                print("Your rate have been recorded successfully!")

                            input("Press Enter to continue...")
                            stage = 0
                        except DBRecordError:
                            print("Error encountered")
                            slots_to_remove = []
                            input("Press Enter to continue...")

    # def bubbleSort(arr,index):
    #     n = len(arr)
    #     for i in range(n):
    #
    #         # Last i elements are already in place
    #         for j in range(0, n - i - 1):
    #
    #             if arr[j][index] > arr[j + 1][index]:
    #                 arr[j], arr[j + 1] = arr[j + 1], arr[j]
    #
    #     arr_sorted = []
    #     for i in range(len(arr)):
    #         arr_sorted.append(arr[i])
    #
    #     return arr_sorted

    # arr = [64, 34, 34, 25, 12, 25, 12, 22, 11, 90]
    # # bubbleSort(arr)
    # # arr_sorted = bubbleSort(arr)
    # print(bubbleSort(arr))



if __name__ == "__main__":
    current_user = MenuHelper.login()
    MenuHelper.dispatcher(current_user["username"], current_user["user_type"])
    Patient(current_user).main_menu()
