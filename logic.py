__author__ = 'V'

from open_questions import get_movies_at_theatre, get_theatres_for_movie
from showtime import string_to_frame, frame_to_time

'''
logic submodule

Logic is thought of in terms of cases: given a limited set of total
attributes to fulfill, we want to fit in as many as possible while also
making sure it is all mutually compatible. case 1: we have one movie, case 1.1: we have a movie
and a theatre, is this movie playing at this theatre? case 2: we have two movies and so on..
order of attempting-to-fit is movies - theatres - time. So it might input a movie
and a theatre and then fail at selecting the chosen time.

narrow() takes in tokeniser output - the tagged movie/theatre/time/day entities
it subcontracts the work. there is a submodule for each attribute, each function
makes sure that what it inputs into the movie request is
correct given all the other information it knows.
each submodule updates the request object based on what it knows. each one creates a
potential return message for the customer.

output of narrow() is given to eval()
finally, decisions: do we have enough information?
which questions must we ask to get more information?
maybe the selected movie is not playing in the selected theatre?
give alternate showtimes
eval() chooses which output to return.


long if/else cases are awkward but it seems to work
'''

'''
helper function for narrow()

update the movie title in the request object,
returns tuple r1 of Int has_correct_movies, message
has_correct_movies code:
0 for no movies
1 for selected 1
2 for more than one
'''
def narrow_movies(req,tag_movs,ntm):
    r1 = 0, "Which movie?"
    if req.done[0] != 1:
        if len(tag_movs) == 1:
            m_nice = ntm[tag_movs[0]].title
            req.add_title(m_nice)
            r1 = 1, ""

         # use for indexing!
        if len(tag_movs) > 1:
            statement = '\n'.join(['{}. {}'.format(i, t) for i, t in enumerate(tag_movs)])
            r1 = 2, "Possible options: " + statement
    return r1

'''
helper function for narrow()

update the movie theatre in the request object
returns tuple r2 of Int has_correct_theatre (0,1, or 2), message
'''
def narrow_theatres(req,tag_theats,ntt):
    mk = req.title.lower()
    r2 = 0, "At which theatre?"
    # take care of theatres, either we find 0, 1 or more than 1
    if len(tag_theats) == 1:
        t = tag_theats[0] # use for indexing!
        t_nice = ntt[t].bms_name

        if req.done[0]:
            # check if movie is in theatre today
            d = ntt[t].movies
            if len(d.get(mk, [])) == 0:
                r2 = 0, "Sorry, but {} isn't showing at {} today.".format(req.title, t_nice)
            else:
                r2 = 1, "Possible showings today: "+ ' '.join([t.printout() for t in d.get(mk)])
                req.add_theatre(t_nice)
        else:
            req.add_theatre(t_nice)
            r2 = 1, ""

    if len(tag_theats) > 1:
        # check which all are playing if movie is mentioned
        # then return subset or full set of tag_theats
        if req.done[0]:
            ft = [t for t in tag_theats if len(ntt[t].movies.get(mk, [])) > 0]
            if len(ft) == 0:
                ft = tag_theats
                statement = "{} isn't playing there today".format(req.title)
            else:
                statement = "{} is playing in: ".format(req.title) \
                            + '\n'.join(['{}. {}'.format(i, t) for i, t in enumerate(ft)])
            r2 = 2, statement
        else:
            statement = "Possible theatre options: " \
                        + '\n'.join(['{}. {}'.format(i, t) for i, t in enumerate(tag_theats)])
            r2 = 2, statement

    return r2

'''
helper function for narrow()

Given at least a movie title, and the list of times/numbers mentioned, try to narrow down
how many tickets and which time to choose

input: r1 and r2 are tuples 0|1|2, Message for movies and theatres
Integer ticket_num, String[] tday, String[] times
returns r3, r4, similar tuples with code, message for number of tickets and times
'''
def narrow_num(req, r1, r2, tday, ticket_num, times, ntt):
    r3 = req.done[1], "How many tickets?"
    r4 = req.done[4], "What time?"
    # number of tickets
    if ticket_num != -1:
        assert(isinstance(ticket_num,int))
        req.add_tickets(ticket_num)
        t_form = "You've got {} ticket{}".format(ticket_num,("" if ticket_num==1 else "s"))
        r3 = 1, t_form

    # pick a showtime or a time of day
    # showtime overrides time of day

    #we have a singular time options
    day,time = len(tday) == 1, len(times) == 1

    '''
    get_options()
    helper function
    #Boolean time
    #lowercase movie title key mk
    #lowercase theatre name key t_nice (if we have it)
    # given a single movie and theatre, and time of day or specific time (which we convert back
    # to time of day
    # if we have a movie and a theatre, see if the time is possible
    # else, if we have just a movie, see which theatres we can go to
    # else, if we have just a theatre, see which movies
    # return a list of times that the movie is playing there
    #returns []Time
    '''
    def get_options(time):
        if time: frames = times[0].ask_frame()
        else: frames = [string_to_frame(tday[0])]

        # at least one of these must not be None!!
        mk = (req.title.lower() if r1[0] else None)
        t_nice = (req.theatre.lower() if r2[0] else None) #todo waaaaayyy too may options
        # maybe it should just remember the time/ time of day and wait until a specific theatre is given

        if t_nice == None:
            options, statement = get_theatres_for_movie(mk, ntt, frames)
        elif mk == None:
            options, statement = get_movies_at_theatre(t_nice,ntt,frames)
        else:
            options, statement = get_movies_at_theatre(t_nice, ntt, frames, mk)
        return options, statement


    # with tday
    if day or time:
        if r1[0] or r2[0]:
            options, statement = get_options(time)
            # we have options for the customer
            # cases for changing the returned statement
            if len(options) == 0:
                r4 = 0, statement
            else:
                showtimes = options[0][1]
                if len(showtimes)==1: req.add_time(showtimes[0])
                r4 = min(len(showtimes),2), statement
        else:
            # no movie, no theatre either
            # just add the time and add functionality in narrow_movies and narrow_theatres for
            # checking time todo
            if day: req.add_time(frame_to_time(string_to_frame(tday[0])))
            if time: req.add_time(times[0])

    # we have multiple time options>>
    if len(times) > 1:
        r4 = 2, "Multiple times selected."

    return r3, r4

'''
narrow()

input: MovieRequest object and several lists of tags. Movie and Theatre names in tags must be
keys into their respective maps. KEYS ARE LOWERCASE
Int ticket_num, Time[] times, tday
dictionaries ntm, ntt
takes and fills in a MovieRequest object based on the most likely.
outputs.
if there is only one movie and/or theatre, input into request, return 1
if there is more than one, send in a question to narrow it down
need to make sure the ticket is valid!

assuming time is for today

returns updated_request, r1, r2, r3, r4
a tuple of results each for movies, theatres, number of tickets and showtimes
'''
def narrow(req, tag_movs, tag_theats, tday, ticket_num, times, ntm, ntt):
    # take care of movies, either we find 0, 1 or more than 1
    #print (tag_movs, tag_theats)
    r1 = narrow_movies(req, tag_movs, ntm)
    r2 = narrow_theatres(req,tag_theats,ntt)
    r3, r4 = narrow_num(req, r1, r2, tday, ticket_num, times, ntt)

    return evaluate(req, r1, r2, r3, r4)


'''
helper function for narrow()

uses all the returned outputs of the previous helper functions
decide what more information is required
passes on final information to the bot
returns a tuple of the new question number,
and a statement to be sent back to the customer

note that req.done checks if we have completed the field
so it may be 0 if we have not heard a response, or if we
have too many possible answers as well

Checks movie, then theatre, then number of tickets, then time
'''
def evaluate(req, r1, r2, r3, r4):
    if not req.done[0]:  # no movie
        return 0, r1[1]
    elif not req.done[2]:  # no theatre
        return 2, r2[1]
    elif not req.done[1]:  # no ticket number
        return 1, r3[1]
    elif not req.done[4]: # no time
        return 4, r4[1]
    else:
        # we are done!
        return -1, req.readout()


print("Logic module loaded")

'''
debugging:

from knowledge import get_theatres
ntm, ntt, tl = get_theatres()
from showtime import *
from open_questions import *
from classes import *

t_nice = ntt.keys()[4]
mk = ntt[t_nice].movies.keys()[0]
req = MovieRequest("test")
req.add_title(mk)
req.add_theatre(t_nice)


#for narrow_num
times = [Time('5pm')]
tday = ['evening']
ticket_num = 3
r1 = [True]
r2 = [True]
narrow_num(req,r1,r2,tday,ticket_num,times,ntt)
r1=[False]
narrow_num(req,r1,r2,tday,ticket_num,times,ntt)

'''''
