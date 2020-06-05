###############################################################################
#### biblioteki ####
###############################################################################
import os
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime , timedelta# do okrelenia daty

###############################################################################
#### Wczytanie danych ####
###############################################################################
# https://data.europa.eu/euodp/pl/data/dataset/covid-19-coronavirus-data/resource/260bbbde-2316-40eb-aec3-7cd7bfc2f590
os.chdir('D:\\KK\\OneDrive\\Wroclaw w Liczbach\\Gotowe projekty\\20200328 Koronawirus')


Dane = pd.read_csv(os.getcwd() + '\\Dane 20200408.csv', \
                       encoding = 'windows-1250', index_col=False, sep = ',',decimal=".")

PL = Dane.loc[Dane['countriesAndTerritories'] == 'Poland', ['dateRep', 'cases']]
###############################################################################
#### Przygotowanie danych ####
###############################################################################
#ustalenie daty
Dane['DATA'] = pd.to_datetime(Dane['dateRep'], format='%d/%m/%Y')


#sortowanie
Dane_sort = Dane.sort_values('DATA', ascending=True)
Dane_sort = Dane_sort.reset_index(drop=True)

#sumowanie  i dodanie sumy chorych oraz smierci
Dane_sort['cumsum_Cases'] = Dane_sort.groupby('geoId')['cases'].cumsum()
Dane_sort['cumsum_Deaths'] = Dane_sort.groupby('geoId')['deaths'].cumsum()

PL = Dane_sort.loc[Dane_sort['countriesAndTerritories'] == 'Poland', ['dateRep', 'cumsum_Cases']]


##############################################################################
#### legend - funkcja z internetu do zmainy kolejnosći legendy####
###############################################################################
#  Returns tuple of handles, labels for axis ax, after reordering them to conform to the label order `order`, 
#and if unique is True, after removing entries with duplicate labels.
def reorderLegend(ax=None,order=None,unique=False):
    if ax is None: ax=plt.gca()
    handles, labels = ax.get_legend_handles_labels()
    labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0])) # sort both labels and handles by labels
    if order is not None: # Sort according to a given list (not necessarily complete)
        keys=dict(zip(order,range(len(order))))
        labels, handles = zip(*sorted(zip(labels, handles), key=lambda t,keys=keys: keys.get(t[0],np.inf)))
    if unique:  labels, handles= zip(*unique_everseen(zip(labels,handles), key = labels)) # Keep only the first of each handle
    ax.legend(handles, labels)
    return(handles, labels)


def unique_everseen(seq, key=None):
    seen = set()
    seen_add = seen.add
    return [x for x,k in zip(seq,key) if not (k in seen or seen_add(k))]

###############################################################################
#### Przygotowanie danych ####
###############################################################################
show_country = 'Poland'
days_past    = -10
days_future  = 10
DATA = Dane_sort['DATA'].max() - timedelta(days = 1)

#aktualnie kraj uwidoczniony ile ma zachorowań
country_show_cases_now = Dane_sort[Dane_sort['countriesAndTerritories'] == show_country]['cumsum_Cases'].max()

#dodanie kolumny roboczej- jezeli dany kraj ma mneij niż Polska teraz to daj -1, w przeciwmym przypadku daj +1
Dane_sort.loc[Dane_sort['cumsum_Cases'] <  country_show_cases_now, 'tmp'] = -1
Dane_sort.loc[Dane_sort['cumsum_Cases'] >= country_show_cases_now, 'tmp'] =  1 

#wybranie tych z zachorowaniami poniżej Polski, żeby wyliczyć minusowe Nday
under = Dane_sort.loc[Dane_sort['cumsum_Cases'] <  country_show_cases_now]
#posortowanie w odwrotnej kolejnosci
under = under.sort_values('DATA', ascending=False).reset_index(drop=True)
#policzenie ile dni do tyłu
under['N_day'] = under.groupby('geoId')['tmp'].cumsum() 
#ograniczenie
under = under[under['N_day'] >= days_past]

#wybranie tych z zachorowaniami powyżej Polski, żeby wyliczyć dodatnie nday
above = Dane_sort.loc[Dane_sort['cumsum_Cases'] >=  country_show_cases_now]
#posortowanie w odwrotnej kolejnosci
above = above.sort_values('DATA', ascending=True).reset_index(drop=True)
#policzenie ile dni do tyłu
above['N_day'] = above.groupby('geoId')['tmp'].cumsum() - 1
#ograniczenie
above = above[above['N_day'] <= days_future]


#lista krajów, które mają wiecej zachorowań niż w Polsce
COUNTRIES_above = above['countriesAndTerritories'].unique()

#połączenie zbiorów danych
tmp = pd.concat([under, above], axis=0, join='outer', ignore_index=False)



#ograniczenia do osi
y_max = tmp[tmp['N_day'] == days_future]['cumsum_Cases'].max()

#wybranie 3 najgorszych scenariuszy
tmp_TOP = tmp[tmp['N_day'] == days_future - 1].sort_values('cumsum_Cases',ascending = False).groupby('N_day').head(4)

#wybranie 3 najlepszych scenariuszy
tmp_BOTTOM = tmp[tmp['N_day'] == days_future - 1].sort_values('cumsum_Cases',ascending = True).groupby('N_day').head(3).sort_values('cumsum_Cases',ascending = False)

###############################################################################
#### Wykres ####
###############################################################################
i = 0
j = 0
for country in COUNTRIES_above:
    #print(country)
    tmp2 = tmp[tmp['countriesAndTerritories'] == country]
    if country == show_country:
        print(country)
        plt.plot('N_day', 'cumsum_Cases', data=tmp2,  label = 'Polska',\
                 color='skyblue', linewidth=4, alpha=1)
        #tmp3 = tmp2
    #top złe kraje
    elif any(tmp_TOP  ['countriesAndTerritories'].str.contains(country)):
        print(country)
        plt.plot('N_day', 'cumsum_Cases', data=tmp2,  label = 'Największe wzrosty' if i == 0 else "",\
                 color='red',    linewidth=1, alpha=0.3)
        i = i + 1
    #top dobre kraje
    elif any(tmp_BOTTOM['countriesAndTerritories'].str.contains(country)):
        print(country)
        plt.plot('N_day', 'cumsum_Cases', data=tmp2,  label = 'Najmniejsze wzrosty' if j == 0 else "",\
                 color='green',    linewidth=1, alpha=0.3)
        j = j + 1
        
    else:
        plt.plot('N_day', 'cumsum_Cases', data=tmp2, label = '_nolegend_',\
                 color='gray',    linewidth=1, alpha=0.2)
        




#### add median 
tmp4 = tmp[tmp['countriesAndTerritories'].isin(COUNTRIES_above)]
tmp4 = tmp4.groupby('N_day')[['cumsum_Cases']].median().reset_index() 

plt.plot('N_day', 'cumsum_Cases', \
         data=tmp4, \
         label = 'Mediana',\
         color='black', linewidth=1, linestyle='dashed', alpha=1)

#set limits
axes = plt.gca()
axes.set_xlim([days_past, days_future])
axes.set_ylim([0, y_max]) 

# legenda     
plt.legend()
reorderLegend(axes,    ['Polska', \
                        'Największe wzrosty', 'Najmniejsze wzrosty', 'Mediana'])
# set plot title
axes.set(title="Dynamika zachorowań COVID-19 na świecie")
# add labels to the axes
axes.set(xlabel="Ilość dni od " + str(country_show_cases_now) + \
         " zachorowań (liczba zachorowań w Polsce na " + \
         str(DATA.strftime("%Y-%m-%d")) + \
         " )" , \
         ylabel="Ilość osób zdiagnozowanych z COVID-19");


plt.savefig(os.getcwd() + '\\Wykres nominalne' + '.png', \
                dpi=300, bbox_inches='tight')
