import discord
import pickle
import lxml.html
import os
import tokens

client = discord.Client()

adminID = tokens.adID
channelID = tokens.chID
primerMissatgeID = tokens.pmID
ready = False

class Participant:
    def __init__(self,ski,name,date):
        self.esqui = ski
        self.casc = False
        self.places_cotxe = 0
        self.tier = 0
        self.botes = True
        self.equip = True
        self.last_message = date
        self.nom = name
        self.DNI = ''
        self.nomComplet = ''
        self.hotel = False

participants = {}

def duplicar(filename,duplicatefilename):
    f = open(filename)
    data = f.read()
    dup = open(duplicatefilename,'w+')
    dup.write(data)
    f.close()
    dup.close()

def parseHTML(id):
    f = open(str(id)+'.htm')
    page = f.read()
    f.close()
    root = lxml.html.fromstring(page)
    result = [0 for i in range(130)]
    llista = root.xpath('//*[starts-with(@id,"btn-")]')
    it = 1
    for i in llista:
        if i.get('style').split()[1] == 'green':
            result[int(i.get('id')[4:])-1] = 2
        elif i.get('style').split()[1] == 'yellow':
            result[int(i.get('id')[4:])-1] = 1
    return result

async def afegir_participant(id,esqui):
    if id in participants.keys():
        return
    duplicar('BaseCalendari.htm',str(id)+'.htm')
    u = await client.fetch_user(id)
    date = (await u.send('Estas apuntat')).created_at
    p = Participant(esqui,u.name,date)
    participants[id] = p
    await embedded_status_message(u)
    save()

async def eliminar_participant(id):
    if id not in participants.keys():
        return
    u = await client.fetch_user(id)
    df = discord.File(str(id) + '.htm',filename=u.name+'.htm')
    await u.send(content='Estas desapuntat, et passo el teu calendari per a que no et calgue omplir-lo altra vegada de zero si més endavant et tornes a apuntar .',files = [df])
    participants.pop(id)
    save()
    os.remove(str(id) + '.htm')

def save():
    f = open('databackup','wb+')
    pickle.dump(participants,f)
    f.close()
    f = open('data','wb+')
    pickle.dump(participants,f)
    f.close()

async def comprovar_participants():
    ids = []
    esqui = []
    missatge = await client.get_channel(channelID).fetch_message(primerMissatgeID)

    for i in missatge.reactions:
        if str(i.emoji) == '⛷️' or str(i.emoji) == '🏂':
            async for j in i.users():
                ids.append(j.id)
                esqui.append(str(i.emoji) == '⛷️')

    for i in range(len(ids)):
        if not ids[i] in participants.keys():
            await afegir_participant(ids[i],esqui[i])

    participantsPerEliminar = []
    for key in participants.keys():
        if not key in ids:
            participantsPerEliminar.append(key)

    for key in participantsPerEliminar:
        await eliminar_participant(key)

@client.event
async def on_guild_join(guild):
    print("JOINED")
    global channelID
    global primerMissatgeID
    if channelID != 0 and primerMissatgeID != 0:
        return
    newChannel = await guild.create_text_channel('Esquiada 22-23')
    channelID = newChannel.id
    newMessage = await newChannel.send('Los que tinguesseu interés en vindre, reaccioneu en ⛷️ o 🏂 pa apuntarvos, si despues se vos lleven les ganes o no teniu diners o lo k sigue, borreu la reaccio i ya.')
    primerMissatgeID = newMessage.id
    print('channelID=',channelID)
    print('messageID=',primerMissatgeID)

@client.event
async def on_ready():
    global ready
    global participants
    print('We have logged in as {0.user}'.format(client))
    if channelID == 0:
        ready = True
        return
    try:
        f = open('data','rb')
        participants = pickle.load(f)
        f.close()
    except:
        await (await client.fetch_user(adminID)).send('Error de unpickling')
        print('Error de unpickling')
        participants = {}
        duplicar('databackup','oldData')
    await comprovar_participants()
    await historial_missatges()
    ready = True

async def status_message(user):
    usuari = participants[user.id]
    missatge = ''

    if usuari.esqui:
        missatge += '⛷️ Faras esqui, pots canviar-ho enviant-me un missatge que digue $snow.\n'
    else:
        missatge += '🏂 Faras snow, pots canviar-ho enviant-me un missatge que digue $esqui.\n'
    
    if usuari.casc:
        missatge += '🪖 Has demanat casc, pots llevar-lo enviant-me un missatge que digue $casc.\n'
    else:
        missatge += '🪖 No has demanat casc, pots afegir-lo enviant-me un missatge que digue $casc.\n'



    if usuari.botes:
        missatge += '👢 Llogaras les botes, si ja en tens i penses portar-te les teues pots canviar-ho enviant-me un missatge que digue $botes.\n'
    else:
        missatge += '👢 No llogaras les botes, si no en tens i vols llogar-les pots fer-ho enviant-me un missatge que digue $botes.\n'

    if usuari.equip:
        missatge += '🎿 Llogaras els esquis/snow. Si ja en tens i penses portar-te el teus de casa, pots canviar-ho enviant-me un missatge que digue $equip.\n'
    else:
        missatge += '🎿 No llogaras els esquis/snow. Si no en tens i vols llogar-los, pots fer-ho enviant-me un missatge que digue $equip.\n'



    if usuari.tier == 0:
        missatge += '🟤 El material que llogues serà de categoria bronze. Aquesta és la categoria més barata i la més adecuada per a principiants, si vols canviar-la pots enviar-me un missatge que digue $categoria plata o $categoria or.\n'
    elif usuari.tier == 1:
        missatge += '⚪ El material que llogues serà de categoria plata. Si vols canviar-la pots enviar-me un missatge que digue $categoria bronze o $categoria or.\n'
    else:
        missatge += '🟠 El material que llogues serà de categoria or. Si vols canviar-la pots enviar-me un missatge que digue $categoria bronze o $categoria plata.\n'
    

    missatge += '🚙 Tens ' + str(usuari.places_cotxe) + ' places al cotxe. Si vols canviar-ho, pots fer-ho enviant-me un missatge que digue $cotxe N on N és el numero de places.\n'
    missatge += '🗓️ Si vols veure la teva disponibilitat, pots demanar-me el calendari enviant-me un missatge que digue $calendari, pots editar-lo des de qualsevol navegador, guardar-lo en Ctrl+S i una vegada modificat lo tornes a enviar per este xat.\n'
    missatge += '📜 Finalment, si en algun moment vols que et torne a enviar aquest missatge, pots fer-ho en $status.'
    
    await user.send(missatge)

def get_num_emoji(n):
    caracters = ['0️⃣','1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟']
    return caracters[min(n,10)]

async def embedded_status_message(user):
    usuari = participants[user.id]
    missatge = discord.Embed(title='ID: ' + user.name + '\nNom i Cognoms: ' + usuari.nomComplet + '\nDNI: ' + usuari.DNI,description = 'Pots posar bé lo DNI en un missatge que digue `$DNI ...` i lo nom en un missatge que digue `$nom ...`')
    num_emoji = get_num_emoji(usuari.places_cotxe)
    if usuari.esqui:
        missatge.add_field(name = '⛷️',value='Faras esqui, pots canviar-ho enviant-me un missatge que digue `$snow`.',inline=False)
    else:
        missatge.add_field(name = '🏂',value='Faras snow, pots canviar-ho enviant-me un missatge que digue `$esqui`.',inline=False)
    
    if usuari.casc:
        missatge.add_field(name = '🪖✅ Casc',value='Has demanat casc, pots llevar-lo enviant-me un missatge que digue `$casc`.')
    else:
        missatge.add_field(name = '🪖❌ Casc',value='No has demanat casc, pots afegir-lo enviant-me un missatge que digue `$casc`.')



    if usuari.botes:
        missatge.add_field(name = '👢✅ Botes',value='Llogaras les botes, si ja en tens i penses portar-te les teues pots canviar-ho enviant-me un missatge que digue `$botes`.')
    else:
        missatge.add_field(name = '👢❌ Botes',value='No llogaras les botes, si no en tens i vols llogar-les pots fer-ho enviant-me un missatge que digue `$botes`.')

    if usuari.equip:
        missatge.add_field(name = '🎿✅ Equip',value='Llogaras els esquis/snow. Si ja en tens i penses portar-te el teus de casa, pots canviar-ho enviant-me un missatge que digue `$equip`.')
    else:
        missatge.add_field(name = '🎿❌ Equip',value='No llogaras els esquis/snow. Si no en tens i vols llogar-los, pots fer-ho enviant-me un missatge que digue `$equip`.')



    if usuari.tier == 0:
        missatge.add_field(name = '🟤 Categoria del material',value='El material que llogues serà de categoria bronze. Aquesta és la categoria més barata i la més adecuada per a principiants, si vols canviar-la pots enviar-me un missatge que digue `$categoria plata` o `$categoria or`.')
    elif usuari.tier == 1:
        missatge.add_field(name = '⚪ Categoria del material',value='El material que llogues serà de categoria plata. Si vols canviar-la pots enviar-me un missatge que digue `$categoria bronze` o `$categoria or`.')
    else:
        missatge.add_field(name = '🟠 Categoria del material',value='El material que llogues serà de categoria or. Si vols canviar-la pots enviar-me un missatge que digue `$categoria bronze` o `$categoria plata`.')
    

    missatge.add_field(name = '🚙'+num_emoji+' Cotxe',value='Tens ' + str(usuari.places_cotxe) + ' places al cotxe. Si vols canviar-ho, pots fer-ho enviant-me un missatge que digue `$cotxe N` on `N` és el numero de places.')
    missatge.add_field(name = '🗓️ Calendari',value= 'Si vols veure la teva disponibilitat, pots demanar-me el calendari enviant-me un missatge que digue `$calendari`, pots editar-lo des de qualsevol navegador, guardar-lo `Ctrl+S`, i una vegada modificat lo tornes a enviar per este xat.')
    
    if usuari.hotel:
        missatge.add_field(name = '🏨 Allotjament',value='Preferixes quedar-te a dormir a un hotel a mitja pensió (més car), si vols canviar-ho a apartament, pots fer-ho enviant el missatge `$allotjament`.')
    else:
        missatge.add_field(name = '🏠 Allotjament',value='Preferixes quedar-te a dormir a un apartament i cuinar-te el menjar (més barat), si vols canviar-ho a hotel mitja pensió, pots fer-ho enviant el missatge `$allotjament`.')

    missatge.add_field(name = '📜',value ='Finalment, si en algun moment vols que et torne a enviar aquest missatge, pots fer-ho en `$status`.', inline = False)
    
    await user.send(embed=missatge)

async def gestionarDM(message):
    if message.author == client.user:
        return
    if message.content.startswith('$status'):
        await embedded_status_message(message.author)
    elif message.content.startswith('$cotxes'):
        await cotxes(message)
    elif message.content.startswith('$cotxe'):
        try:
            n = int(message.content.split()[1])
        except:
            return
        if n < 0:
            await message.author.send('No')
        else:
            participants[message.author.id].places_cotxe = n
            if n == 0:
                await message.author.send('Has canviat el nombre de places al cotxe a 0. És a dir, que no portes cotxe')
            else:
                await message.author.send('Has canviat el nombre de places al cotxe a ' + str(n)+ '. És a dir, tu a la plaça del conductor i ' + str(n-1) +' més.')
    elif message.content.startswith('$casc'):
        if participants[message.author.id].casc:
            participants[message.author.id].casc = False
            await message.author.send('Casc eliminat')
        else:
            participants[message.author.id].casc = True
            await message.author.send('Casc afegit')
    elif message.content.startswith('$esqui'):
        if participants[message.author.id].esqui:
            await message.author.send('Ja fas esqui')
        else:
            participants[message.author.id].esqui = True
            await message.author.send('Ara faras esqui')
    elif message.content.startswith('$snow'):
        if participants[message.author.id].esqui:
            participants[message.author.id].esqui = False
            await message.author.send('Ara faras snow')
        else:
            await message.author.send('Ja fas snow')
    elif message.content.startswith('$botes'):
        if participants[message.author.id].botes:
            participants[message.author.id].botes = False
            await message.author.send('Botes eliminades')
        else:
            participants[message.author.id].botes = True
            await message.author.send('Botes afegides')
    elif message.content.startswith('$equip'):
        if participants[message.author.id].equip:
            participants[message.author.id].equip = False
            await message.author.send('Equip eliminat')
        else:
            participants[message.author.id].equip = True
            await message.author.send('Equip afegit')
    elif message.content.startswith('$categoria'):
        tier = message.content.split()[1]
        if tier == 'bronze':
            participants[message.author.id].tier = 0
            await message.author.send('Has seleccionat categoria bronze')
        elif tier == 'plata':
            participants[message.author.id].tier = 1
            await message.author.send('Has seleccionat categoria plata')
        elif tier == 'or':
            participants[message.author.id].tier = 2
            await message.author.send('Has seleccionat categoria or')
        else:
            await message.author.send(tier + ' no és cap categoria')
    elif message.content.startswith('$calendari'):
        df = discord.File(str(message.author.id) + '.htm',filename=message.author.name+'.htm')
        await message.author.send(files = [df])
    elif len(message.attachments) == 1 and message.attachments[0].filename[-4:] == '.htm':
        await message.attachments[0].save(str(message.author.id) + '.htm')
        await message.author.send('Calendari rebut')
    elif message.content.startswith('$hello'):
        await message.channel.send('Hi!')
    elif message.content.startswith('$dies'):
        await calcul_dies(message)
    elif message.content.startswith('$dia'):
        await dispo_dia(message)
    elif message.content.startswith('$extra'):
        f = open('logs.txt','a+')
        f.write(message.author.name + ' ' + str(message.created_at) + ' ' + message.content[7:] + '\n')
        f.close()
        await message.author.send('Rebut: '+message.content[7:])
    elif message.content.startswith('$nom'):
        participants[message.author.id].nomComplet = message.content[4:]
        await message.author.send('El teu nom complet és: '+message.content[4:])
    elif message.content.startswith('$DNI'):
        participants[message.author.id].DNI = message.content[4:]
        await message.author.send('El teu DNI és: '+message.content[4:])
    elif message.content.startswith('$allotjament'):
        if participants[message.author.id].hotel:
            participants[message.author.id].hotel = False
            await message.author.send('Has canviat a apartament')
        else:
            participants[message.author.id].hotel = True
            await message.author.send('Has canviat a hotel mitja pensió')


async def historial_missatges():
    for id in participants.keys():
        user = await client.fetch_user(id)
        message_list = []
        async for message in user.history(limit=20):
            if message.created_at > participants[id].last_message:
                message_list.append(message)
        for m in message_list[::-1]:
            await gestionarDM(m)
            participants[id].last_message = m.created_at
            save()

async def calcul_dies(message):
    #min(cars,g+y),green,yellow,g+y,cars,day
    result = [[0,0,0,0,0,i] for i in range(130)]
    for id in participants.keys():
        user_result = parseHTML(id)
        for i in range(130):
            if user_result[i] == 1:
                result[i][2] += 1
                result[i][4] += participants[id].places_cotxe
            elif user_result[i] == 2:
                result[i][1] += 1
                result[i][4] += participants[id].places_cotxe
    for i in range(130):
        result[i][3] = result[i][1] + result[i][2]
        result[i][0] = min(result[i][3],result[i][4])
            
    result.sort(reverse = True)
    emb_mess = discord.Embed(title='🗓️ dies')
    for dia in result[0:10]:
        emb_mess.add_field(name = 'Dia'+str(dia[5]+1)+', '+str(dia[0])+'persones',value=str(dia[1])+'🟢   '+str(dia[2])+'🟡   '+str(dia[4])+'🚙')
    await message.channel.send(embed= emb_mess)

async def cotxes(message):
    emb_mess = discord.Embed(title='🚙 cotxes')
    total = 0
    body = ''
    for id in participants.keys():
        if participants[id].places_cotxe > 0:
            body += get_num_emoji(participants[id].places_cotxe)+' '+participants[id].nom+'\n'
            total += participants[id].places_cotxe
    emb_mess.add_field(name='Conductors',value=body)
    emb_mess.add_field(name='Total',value = str(total)+' places',inline=False)
    await message.channel.send(embed = emb_mess)

async def dispo_dia(message):
    try:
        d = int(message.content.split()[1])-1
    except:
        return
    if d < 0 or d > 129:
        return
    emb_mess = discord.Embed(title='Dia '+str(d+1))
    verd = ''
    groc = ''
    roig = ''
    for id in participants.keys():
        val = parseHTML(id)[d]
        if val == 0:
            roig += participants[id].nom+'\n'
        elif val == 1:
            groc += participants[id].nom+'\n'
        elif val == 2:
            verd += participants[id].nom+'\n'
    if verd == '':
        verd = 'ningu'
    if groc == '':
        groc = 'ningu'
    if roig == '':
        roig = 'ningu'
    emb_mess.add_field(name = '🟢',value=verd,inline=False)
    emb_mess.add_field(name = '🟡',value=groc,inline=False)
    emb_mess.add_field(name = '🔴',value=roig,inline=False)
    await message.channel.send(embed = emb_mess)

@client.event
async def on_message(message):
    if message.author == client.user or not ready:
        return
    
    if message.author.id == adminID:
        if message.content.startswith('$quit'):
            save()
            await client.close()
        if message.content.startswith('$exit'):
            await client.close()
        if message.content.startswith('$sendall'):
            body = message.content[9:]
            for id in participants.keys():
                await (await client.fetch_user(id)).send(body)


    if isinstance(message.channel, discord.channel.DMChannel) and message.author.id in participants.keys():
        await gestionarDM(message)
        participants[message.author.id].last_message = message.created_at
        save()
    elif isinstance(message.channel, discord.channel.DMChannel) and message.author.id not in participants.keys():
        await message.author.send('No estas apuntat, pots apuntar-te reaccionant ⛷️ o 🏂 al missatge del canal')


    else:
        if message.channel.id == channelID:
            if message.content.startswith('$dies'):
                await calcul_dies(message)
            elif message.content.startswith('$cotxes'):
                await cotxes(message)
            elif message.content.startswith('$dia'):
                await dispo_dia(message)


@client.event
async def on_raw_reaction_add(payload):
    if not ready:
        return
    if payload.channel_id == channelID and payload.message_id == primerMissatgeID and (str(payload.emoji) == '⛷️' or str(payload.emoji) == '🏂'):
        await afegir_participant(payload.user_id,str(payload.emoji) == '⛷️')

@client.event 
async def on_raw_reaction_remove(payload):
    if not ready:
        return
    message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
    if payload.channel_id == channelID and payload.message_id == primerMissatgeID and str(payload.emoji) == '⛷️' and payload.user_id not in [user.id for users in [await reaction.users().flatten() for reaction in message.reactions if str(reaction.emoji) == '🏂'] for user in users]:
        await eliminar_participant(payload.user_id)
    if payload.channel_id == channelID and payload.message_id == primerMissatgeID and str(payload.emoji) == '🏂' and payload.user_id not in [user.id for users in [await reaction.users().flatten() for reaction in message.reactions if str(reaction.emoji) == '⛷️'] for user in users]:
        await eliminar_participant(payload.user_id)

client.run(tokens.token)
